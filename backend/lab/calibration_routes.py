from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from .auth import Current, Db, Supervisor, Technician
from .calibration_models import Calibration, FitAttempt, ReleaseSlot
from .calibration_schema import FitRequest
from .calibration_service import create_candidate, map_attempt, map_calibration, publish

router = APIRouter(prefix="/calibrations", tags=["分位系数"])


@router.get("")
def versions(db: Db, _operator: Current, probe_id: int | None = None):
    query = select(Calibration).order_by(Calibration.id.desc())
    if probe_id is not None:
        query = query.where(Calibration.probe_id == probe_id)
    return [map_calibration(row) for row in db.scalars(query.limit(80))]


@router.get("/active")
def released(db: Db, _operator: Current):
    query = select(Calibration).join(ReleaseSlot, ReleaseSlot.calibration_id == Calibration.id)
    return [map_calibration(row, with_model=False) for row in db.scalars(query.order_by(ReleaseSlot.day.desc()))]


@router.get("/{calibration_id}")
def version(calibration_id: int, db: Db, _operator: Current):
    row = db.get(Calibration, calibration_id)
    if row is None:
        raise HTTPException(404, "找不到换算候选。")
    return map_calibration(row)


@router.get("/{calibration_id}/attempts")
def attempts(calibration_id: int, db: Db, _operator: Current):
    if db.get(Calibration, calibration_id) is None:
        raise HTTPException(404, "找不到换算候选。")
    query = select(FitAttempt).where(FitAttempt.calibration_id == calibration_id).order_by(FitAttempt.id.desc())
    return [map_attempt(row) for row in db.scalars(query)]


@router.post("", status_code=202)
def fit(data: FitRequest, db: Db, operator: Technician):
    return map_calibration(create_candidate(db, data, operator.username))


@router.post("/{calibration_id}/publish")
def approve(calibration_id: int, db: Db, operator: Supervisor):
    return map_calibration(publish(db, calibration_id, operator.username))
