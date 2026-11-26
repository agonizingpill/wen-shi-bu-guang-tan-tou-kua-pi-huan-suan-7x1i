from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ReferenceSegment(Base):
    __tablename__ = "reference_segments"
    __table_args__ = (
        UniqueConstraint("probe_id", "day", "mode", "start_minute", name="unique_reference_slot"),
        CheckConstraint("start_minute BETWEEN 0 AND 1430 AND MOD(start_minute, 10) = 0", name="valid_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probe_id: Mapped[int] = mapped_column(ForeignKey("probes.id"))
    day: Mapped[date] = mapped_column(Date)
    mode: Mapped[str] = mapped_column(String(8))
    start_minute: Mapped[int] = mapped_column(Integer)
    reference_serial: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(16))
    captured_by: Mapped[str] = mapped_column(String(32))
    witnessed_by: Mapped[str | None] = mapped_column(String(32))
    witness_note: Mapped[str | None] = mapped_column(String(180))
    points: Mapped[list["ReferencePoint"]] = relationship(
        cascade="all, delete-orphan", order_by="ReferencePoint.offset_seconds", lazy="selectin",
    )


class ReferencePoint(Base):
    __tablename__ = "reference_points"
    __table_args__ = (
        UniqueConstraint("segment_id", "offset_seconds", name="one_pair_per_offset"),
        CheckConstraint("offset_seconds BETWEEN 0 AND 599", name="valid_offset_seconds"),
        CheckConstraint("raw_lux >= 0 AND reference_lux >= 0", name="valid_lux_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("reference_segments.id"))
    offset_seconds: Mapped[int] = mapped_column(Integer)
    raw_lux: Mapped[float] = mapped_column(Float)
    reference_lux: Mapped[float] = mapped_column(Float)
