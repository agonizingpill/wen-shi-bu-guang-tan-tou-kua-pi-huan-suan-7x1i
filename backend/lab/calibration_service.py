import logging
from uuid import uuid4

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import delete, select

from .audit import record
from .calibration_models import Calibration, CalibrationSource, FitAttempt, ReleaseSlot
from .constants import CalibrationState, SegmentState
from .installation import require_probe
from .quantile_map import InvalidReference, build_mapping, require_coverage, sample_digest
from .segment_models import ReferenceSegment
from .settings import CHANNEL, REDIS_URL

logger = logging.getLogger("light.calibration")


def map_calibration(row, *, with_model=True):
    return {"id": row.id, "probe_id": row.probe_id, "mode": row.mode,
            "reference_day": row.reference_day.isoformat(), "release_day": row.release_day.isoformat(),
            "start_minute": row.start_minute, "end_minute": row.end_minute, "version": row.version,
            "state": row.state, "submitted_by": row.submitted_by, "approved_by": row.approved_by,
            "explanation": row.explanation, "segment_ids": sorted(s.segment_id for s in row.segments),
            "model": row.model if with_model else None}


def map_attempt(row):
    return {"id": row.id, "calibration_id": row.calibration_id, "outcome": row.outcome,
            "explanation": row.explanation, "segment_ids": row.segment_ids,
            "input_sha256": row.input_sha256,
            "fitted_at": row.fitted_at.isoformat() if row.fitted_at else None}


def wake_worker(*calibration_ids):
    if not calibration_ids:
        return
    try:
        Redis.from_url(REDIS_URL, socket_timeout=2, socket_connect_timeout=2).lpush(CHANNEL, *calibration_ids)
    except RedisError:
        logger.warning("Redis unavailable; worker polls durable candidates %s", calibration_ids)


def create_candidate(db, data, actor):
    probe = require_probe(db, data.probe_id, lock=True)
    if not probe.enabled:
        raise HTTPException(409, "暂停的探头不能拟合新换算。")
    row = Calibration(**data.model_dump(), version="Q-" + uuid4().hex[:12].upper(),
                      state=CalibrationState.QUEUED, submitted_by=actor)
    db.add(row)
    record(db, actor, "queue_fit", row.version)
    db.commit()
    wake_worker(row.id)
    return row


def witnessed_segments(db, candidate):
    return list(db.scalars(select(ReferenceSegment).where(
        ReferenceSegment.probe_id == candidate.probe_id, ReferenceSegment.day == candidate.reference_day,
        ReferenceSegment.mode == candidate.mode, ReferenceSegment.start_minute >= candidate.start_minute,
        ReferenceSegment.start_minute < candidate.end_minute,
        ReferenceSegment.state == SegmentState.WITNESSED,
    ).order_by(ReferenceSegment.start_minute)))


def record_attempt(db, candidate, segments):
    """登记本次拟合用到的采样与结果；后台重试碰上同一组采样时不重复登记。"""
    digest = sample_digest(segments)
    existing = db.scalar(select(FitAttempt).where(
        FitAttempt.calibration_id == candidate.id, FitAttempt.input_sha256 == digest))
    if existing is not None:
        return existing
    attempt = FitAttempt(calibration_id=candidate.id, outcome=candidate.state,
                         explanation=candidate.explanation,
                         segment_ids=[s.id for s in segments], input_sha256=digest)
    db.add(attempt)
    return attempt


def try_fit(db):
    row = db.scalar(select(Calibration).where(Calibration.state == CalibrationState.QUEUED)
                    .order_by(Calibration.id).limit(1).with_for_update(skip_locked=True))
    if row is None:
        return False
    segments = witnessed_segments(db, row)
    try:
        require_coverage(row.start_minute, row.end_minute, segments)
        row.model = build_mapping(segments)
    except InvalidReference as exc:
        row.state, row.explanation, row.model = CalibrationState.REJECTED, str(exc), None
    else:
        row.state, row.explanation = CalibrationState.READY, "连续见证齐备，等待班长签发。"
    record_attempt(db, row, segments)
    db.execute(delete(CalibrationSource).where(CalibrationSource.calibration_id == row.id))
    if row.state == CalibrationState.READY:
        db.add_all([CalibrationSource(calibration_id=row.id, segment_id=s.id) for s in segments])
    record(db, "worker", "fit_" + row.state, row.version)
    db.commit()
    return True


def candidates_covering(db, segment, states):
    """窗口覆盖该采样段的候选，按状态过滤并加行锁（与正在拟合的 worker 串行）。"""
    return db.scalars(select(Calibration).where(
        Calibration.probe_id == segment.probe_id, Calibration.reference_day == segment.day,
        Calibration.mode == segment.mode, Calibration.start_minute <= segment.start_minute,
        Calibration.end_minute > segment.start_minute, Calibration.state.in_(states),
    ).with_for_update())


def stall_for_recapture(db, segment, actor):
    """撤回见证后，用过该段的候选退回等待补采；现行已签发版本不受影响。"""
    stalled = []
    for candidate in candidates_covering(db, segment, (
            CalibrationState.QUEUED, CalibrationState.READY, CalibrationState.REJECTED)):
        candidate.state = CalibrationState.AWAITING_RECAPTURE
        candidate.explanation = f"见证 {segment.source} 已撤回，等待补采见证齐全后重算。"
        record(db, actor, "await_recapture", candidate.version)
        stalled.append(candidate.id)
    return stalled


def requeue_awaiting(db, segment, actor):
    """补采见证齐全后，等待中的候选在原记录下重新排队拟合。"""
    requeued = []
    for candidate in candidates_covering(db, segment, (CalibrationState.AWAITING_RECAPTURE,)):
        try:
            require_coverage(candidate.start_minute, candidate.end_minute, witnessed_segments(db, candidate))
        except InvalidReference:
            continue
        candidate.state = CalibrationState.QUEUED
        candidate.explanation = "补采见证齐全，重新排队拟合。"
        record(db, actor, "requeue_fit", candidate.version)
        requeued.append(candidate.id)
    return requeued


def current_slot(db, probe_id, day, mode, *, lock=False):
    query = select(ReleaseSlot).where(ReleaseSlot.probe_id == probe_id, ReleaseSlot.day == day, ReleaseSlot.mode == mode)
    return db.scalar(query.with_for_update() if lock else query)


def publish(db, calibration_id, actor):
    candidate = db.get(Calibration, calibration_id)
    if candidate is None:
        raise HTTPException(404, "找不到换算候选。")
    probe = require_probe(db, candidate.probe_id, lock=True)
    db.refresh(candidate, with_for_update=True)
    if not probe.enabled:
        raise HTTPException(409, "探头已暂停，无法替换现行版本。")
    if candidate.state != CalibrationState.READY:
        raise HTTPException(409, "仅连续见证并拟合通过的候选可发布；现行版本保留。")
    if candidate.submitted_by == actor:
        raise HTTPException(409, "签发人须独立于拟合提交人。")
    slot = current_slot(db, candidate.probe_id, candidate.release_day, candidate.mode, lock=True)
    if slot:
        old = db.get(Calibration, slot.calibration_id)
        if (old.start_minute, old.end_minute) != (candidate.start_minute, candidate.end_minute):
            raise HTTPException(409, "替换版本必须覆盖相同生效窗口，避免切换后出现时段缺口。")
        old.state = CalibrationState.RETIRED
        slot.calibration_id = candidate.id
    else:
        db.add(ReleaseSlot(probe_id=candidate.probe_id, day=candidate.release_day,
                           mode=candidate.mode, calibration_id=candidate.id))
    candidate.state, candidate.approved_by = CalibrationState.ACTIVE, actor
    record(db, actor, "publish_mapping", candidate.version)
    db.commit()
    return candidate
