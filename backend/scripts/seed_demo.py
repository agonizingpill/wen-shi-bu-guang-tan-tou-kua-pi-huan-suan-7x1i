import json

from sqlalchemy import func, select

from lab.auth import hash_password
from lab.calibration_models import Calibration, CalibrationSource, ReleaseSlot
from lab.constants import CalibrationState, Mode
from lab.database import initialize, open_session
from lab.identity_models import Operator
from lab.installation_models import Probe
from lab.quantile_map import adjust, build_mapping
from lab.readings_models import ConversionReceipt
from lab.segment_models import ReferencePoint, ReferenceSegment
from lab.settings import SEED_PASSWORD

from .demo_fixtures import ACCOUNTS, EAST_PROBE, PROBES, REFERENCE_DAY, RELEASE_DAY, captures


def add_operators(db):
    for username, display_name, role in ACCOUNTS:
        if db.scalar(select(Operator).where(Operator.username == username)) is None:
            db.add(Operator(username=username, role=role, display_name=display_name,
                            password_digest=hash_password(SEED_PASSWORD)))
    db.flush()


def add_probes(db):
    probes = {}
    for attrs in PROBES:
        row = db.scalar(select(Probe).where(Probe.code == attrs["code"]))
        if row is None:
            row = Probe(**attrs)
            db.add(row)
            db.flush()
        probes[row.code] = row.id
    return probes


def add_captures(db, probes):
    for code, mode, start, serial, source, state, values in captures():
        probe_id = probes[code]
        query = select(ReferenceSegment).where(
            ReferenceSegment.probe_id == probe_id, ReferenceSegment.day == REFERENCE_DAY,
            ReferenceSegment.mode == mode, ReferenceSegment.start_minute == start,
        )
        if db.scalar(query) is not None:
            continue
        db.add(ReferenceSegment(
            probe_id=probe_id, day=REFERENCE_DAY, mode=mode, start_minute=start,
            reference_serial=serial, source=source, state=state, captured_by="yu", witnessed_by="tang",
            witness_note="LED 稳定后，与基准表同秒采样。",
            points=[ReferencePoint(**point) for point in values],
        ))
    db.flush()


def add_active_example(db, probe_id):
    row = db.scalar(select(Calibration).where(Calibration.version == "Q-DEMO-EAST"))
    if row is not None:
        return
    segments = list(db.scalars(select(ReferenceSegment).where(
        ReferenceSegment.probe_id == probe_id, ReferenceSegment.day == REFERENCE_DAY,
        ReferenceSegment.mode == Mode.HIGH, ReferenceSegment.state == "witnessed",
        ReferenceSegment.start_minute.in_((360, 370, 380)),
    ).order_by(ReferenceSegment.start_minute)))
    if len(segments) != 3:
        return
    model = build_mapping(segments)
    row = Calibration(
        probe_id=probe_id, mode=Mode.HIGH, reference_day=REFERENCE_DAY, release_day=RELEASE_DAY,
        start_minute=360, end_minute=390, version="Q-DEMO-EAST", state=CalibrationState.ACTIVE,
        submitted_by="yu", approved_by="tang", model=model, explanation="东棚早班的现行亮档换算。",
        segments=[CalibrationSource(segment_id=s.id) for s in segments],
    )
    db.add(row)
    db.flush()
    db.add(ReleaseSlot(probe_id=probe_id, day=RELEASE_DAY, mode=Mode.HIGH, calibration_id=row.id))
    db.add(ConversionReceipt(
        probe_id=probe_id, calibration_id=row.id, day=RELEASE_DAY, mode=Mode.HIGH, minute=361,
        raw_lux=480, adjusted_lux=round(float(adjust(model, [480])[0]), 2), entered_by="yu",
    ))


def seed():
    with open_session() as db:
        add_operators(db)
        probes = add_probes(db)
        add_captures(db, probes)
        add_active_example(db, probes[EAST_PROBE])
        db.commit()
        tracked = (Operator, Probe, ReferenceSegment, ReferencePoint, Calibration, ReleaseSlot, ConversionReceipt)
        return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) for model in tracked}


if __name__ == "__main__":
    initialize()
    print(json.dumps(seed(), sort_keys=True))
