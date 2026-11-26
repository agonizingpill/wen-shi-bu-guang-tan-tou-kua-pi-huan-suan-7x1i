from fastapi import APIRouter
from sqlalchemy import select

from .auth import Current, Db, Supervisor, Technician
from .segment_models import ReferenceSegment
from .segment_schema import CaptureSegment, WitnessNote
from .segment_service import capture, discard, load_segment, map_recall, map_segment, recall, witness

router = APIRouter(prefix="/segments", tags=["亮暗见证"])


@router.get("")
def list_segments(db: Db, _operator: Current, probe_id: int | None = None):
    query = select(ReferenceSegment).order_by(ReferenceSegment.day.desc(), ReferenceSegment.start_minute)
    if probe_id is not None:
        query = query.where(ReferenceSegment.probe_id == probe_id)
    return [map_segment(s) for s in db.scalars(query.limit(150))]


@router.post("", status_code=201)
def add_segment(data: CaptureSegment, db: Db, operator: Technician):
    return map_segment(capture(db, data, operator.username))


@router.post("/{segment_id}/witness")
def witness_segment(segment_id: int, data: WitnessNote, db: Db, operator: Supervisor):
    return map_segment(witness(db, segment_id, data.note, operator.username))


@router.post("/{segment_id}/recall")
def recall_segment(segment_id: int, data: WitnessNote, db: Db, operator: Supervisor):
    return map_segment(recall(db, segment_id, data.note, operator.username))


@router.get("/{segment_id}/recalls")
def recall_archive(segment_id: int, db: Db, _operator: Current):
    return [map_recall(row) for row in load_segment(db, segment_id).recalls]


@router.post("/{segment_id}/discard")
def discard_segment(segment_id: int, data: WitnessNote, db: Db, operator: Supervisor):
    return map_segment(discard(db, segment_id, data.note, operator.username))
