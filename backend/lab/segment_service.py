from fastapi import HTTPException
from sqlalchemy import select

from .audit import record
from .constants import SegmentState
from .installation import require_probe
from .segment_models import ReferencePoint, ReferenceSegment


def load_segment(db, segment_id, *, lock=False):
    query = select(ReferenceSegment).where(ReferenceSegment.id == segment_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None:
        raise HTTPException(404, "找不到所选采样段。")
    return row


def map_segment(row):
    return {"id": row.id, "probe_id": row.probe_id, "day": row.day.isoformat(), "mode": row.mode,
            "start_minute": row.start_minute, "reference_serial": row.reference_serial, "source": row.source,
            "state": row.state, "captured_by": row.captured_by, "witnessed_by": row.witnessed_by,
            "witness_note": row.witness_note,
            "points": [{"offset_seconds": p.offset_seconds, "raw_lux": p.raw_lux,
                        "reference_lux": p.reference_lux} for p in row.points]}


def capture(db, data, actor):
    probe = require_probe(db, data.probe_id, lock=True)
    if not probe.enabled:
        raise HTTPException(409, "探头已暂停，不能登记新的采样段。")
    existing = db.scalar(select(ReferenceSegment).where(
        ReferenceSegment.probe_id == data.probe_id, ReferenceSegment.day == data.day,
        ReferenceSegment.mode == data.mode, ReferenceSegment.start_minute == data.start_minute,
    ))
    if existing and existing.state != SegmentState.DISCARDED:
        raise HTTPException(409, "该时段已登记。作废待见证段后可重采。")
    row = existing or ReferenceSegment(probe_id=data.probe_id, day=data.day, mode=data.mode,
                                       start_minute=data.start_minute)
    row.reference_serial, row.source, row.captured_by = data.reference_serial, data.source, actor
    row.state, row.witness_note, row.witnessed_by = SegmentState.DRAFT, None, None
    if existing:
        row.points.clear()
        db.flush()
    row.points.extend(ReferencePoint(**point.model_dump()) for point in data.points)
    db.add(row)
    record(db, actor, "capture_segment", data.source)
    db.commit()
    return row


def witness(db, segment_id, note, actor):
    row = load_segment(db, segment_id, lock=True)
    if row.state != SegmentState.DRAFT:
        raise HTTPException(409, "仅待见证段可签字。")
    probe = require_probe(db, row.probe_id)
    if row.captured_by == actor:
        raise HTTPException(409, "采样人不能见证自己的记录。")
    if row.reference_serial != probe.reference_serial:
        raise HTTPException(409, f"基准表序列号不匹配，当前安装点要求 {probe.reference_serial}。")
    row.state, row.witnessed_by, row.witness_note = SegmentState.WITNESSED, actor, note
    record(db, actor, "witness_segment", row.source)
    db.commit()
    return row


def discard(db, segment_id, note, actor):
    row = load_segment(db, segment_id, lock=True)
    if row.state != SegmentState.DRAFT:
        raise HTTPException(409, "已见证采样段属于可追溯证据，不可作废。")
    row.state, row.witness_note = SegmentState.DISCARDED, note
    record(db, actor, "discard_segment", row.source)
    db.commit()
    return row
