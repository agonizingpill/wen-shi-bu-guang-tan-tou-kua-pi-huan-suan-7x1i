import csv
import io
from datetime import date

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from .audit import record
from .auth import CanCapture, Current, Db
from .calibration_models import Calibration
from .calibration_service import current_slot
from .constants import Mode
from .installation import require_probe
from .installation_models import Probe
from .quantile_map import adjust
from .readings_models import ConversionReceipt

router = APIRouter(prefix="/readings", tags=["补光交接"])


class RawReading(BaseModel):
    probe_id: int = Field(gt=0)
    day: date
    mode: Mode
    minute: int = Field(ge=0, le=1439)
    raw_lux: float = Field(ge=0, le=100000, allow_inf_nan=False)


def list_receipts(db, day=None):
    query = select(ConversionReceipt, Calibration.version).join(
        Calibration, Calibration.id == ConversionReceipt.calibration_id,
    ).order_by(ConversionReceipt.day.desc(), ConversionReceipt.minute.desc())
    if day is not None:
        query = query.where(ConversionReceipt.day == day)
    return db.execute(query.limit(500))


def receipt(row, version):
    return {"id": row.id, "probe_id": row.probe_id, "calibration_id": row.calibration_id, "version": version,
            "day": row.day.isoformat(), "mode": row.mode, "minute": row.minute, "raw_lux": row.raw_lux,
            "adjusted_lux": row.adjusted_lux, "entered_by": row.entered_by}


@router.get("")
def get_readings(db: Db, _operator: Current):
    return [receipt(row, version) for row, version in list_receipts(db)]


@router.post("", status_code=201)
def convert(data: RawReading, db: Db, operator: CanCapture):
    probe = require_probe(db, data.probe_id, lock=True)
    if not probe.enabled:
        raise HTTPException(409, "该探头已停用，不能签发新读数。")
    slot = current_slot(db, data.probe_id, data.day, data.mode)
    if slot is None:
        raise HTTPException(409, "该日和亮暗档没有有效换算单。")
    calibration = db.get(Calibration, slot.calibration_id)
    if not calibration.start_minute <= data.minute < calibration.end_minute:
        raise HTTPException(409, "读数时间不在已签发换算窗口，不能外推。")
    if not calibration.model["raw_knots"][0] <= data.raw_lux <= calibration.model["raw_knots"][-1]:
        raise HTTPException(409, "原始读数超出见证样本范围，需要补采，不能外推。")
    converted = round(float(adjust(calibration.model, [data.raw_lux])[0]), 2)
    row = ConversionReceipt(**data.model_dump(), calibration_id=calibration.id,
                            adjusted_lux=converted, entered_by=operator.username)
    db.add(row)
    record(db, operator.username, "convert_reading", f"{probe.code}/{data.day}/{data.minute}")
    db.commit()
    return receipt(row, calibration.version)


@router.get("/export")
def dispatch(day: date, db: Db, _operator: Current):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["day", "probe_code", "mode", "minute", "raw_lux", "adjusted_lux", "version"])
    probe_codes = {row.id: row.code for row in db.scalars(select(Probe))}
    for row, version in list_receipts(db, day):
        writer.writerow([row.day, probe_codes[row.probe_id], row.mode, row.minute, row.raw_lux, row.adjusted_lux, version])
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="light-shift-{day.isoformat()}.csv"'})
