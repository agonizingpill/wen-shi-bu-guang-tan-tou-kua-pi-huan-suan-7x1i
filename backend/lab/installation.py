from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from .audit import record
from .auth import Current, Db, Supervisor
from .installation_models import Probe

router = APIRouter(prefix="/probes", tags=["安装台账"])
Serial = Annotated[str, StringConstraints(to_upper=True, pattern=r"^[A-Z0-9][A-Z0-9-]{2,31}$")]


class Mount(BaseModel):
    code: Serial = Field(max_length=24)
    bay: str = Field(min_length=2, max_length=40)
    batch: Serial = Field(max_length=30)
    reference_serial: Serial
    mount_cm: int = Field(ge=15, le=300)


def map_probe(probe):
    return {"id": probe.id, "code": probe.code, "bay": probe.bay, "batch": probe.batch,
            "reference_serial": probe.reference_serial, "mount_cm": probe.mount_cm, "enabled": probe.enabled}


def require_probe(db: Session, probe_id: int, *, lock: bool = False) -> Probe:
    query = select(Probe).where(Probe.id == probe_id)
    if lock:
        query = query.with_for_update()
    probe = db.scalar(query)
    if probe is None:
        raise HTTPException(404, "找不到该探头。")
    return probe


@router.get("")
def list_probes(db: Db, _operator: Current):
    return [map_probe(row) for row in db.scalars(select(Probe).order_by(Probe.code))]


@router.post("", status_code=201)
def mount(data: Mount, db: Db, operator: Supervisor):
    probe = Probe(**data.model_dump())
    db.add(probe)
    record(db, operator.username, "mount_probe", data.code)
    db.commit()
    return map_probe(probe)


@router.post("/{probe_id}/suspend")
def suspend(probe_id: int, db: Db, operator: Supervisor):
    probe = require_probe(db, probe_id, lock=True)
    if probe.enabled:
        probe.enabled = False
        record(db, operator.username, "suspend_probe", probe.code)
        db.commit()
    return map_probe(probe)
