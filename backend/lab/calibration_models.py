from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Calibration(Base):
    __tablename__ = "calibrations"
    __table_args__ = (
        CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute",
                        name="valid_calibration_window"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probe_id: Mapped[int] = mapped_column(ForeignKey("probes.id"))
    mode: Mapped[str] = mapped_column(String(8))
    reference_day: Mapped[date] = mapped_column(Date)
    release_day: Mapped[date] = mapped_column(Date)
    start_minute: Mapped[int] = mapped_column(Integer)
    end_minute: Mapped[int] = mapped_column(Integer)
    version: Mapped[str] = mapped_column(String(20), unique=True)
    state: Mapped[str] = mapped_column(String(24), index=True)
    submitted_by: Mapped[str] = mapped_column(String(32))
    approved_by: Mapped[str | None] = mapped_column(String(32))
    explanation: Mapped[str | None] = mapped_column(String(250))
    model: Mapped[dict | None] = mapped_column(JSON)
    segments: Mapped[list["CalibrationSource"]] = relationship(lazy="selectin")


class CalibrationSource(Base):
    __tablename__ = "calibration_sources"

    calibration_id: Mapped[int] = mapped_column(ForeignKey("calibrations.id"), primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("reference_segments.id"), primary_key=True)


class FitAttempt(Base):
    """每次拟合的留痕：用了哪些采样段、结果如何。同一组采样不重复登记。"""

    __tablename__ = "fit_attempts"
    __table_args__ = (
        UniqueConstraint("calibration_id", "input_sha256", name="unique_attempt_input"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    calibration_id: Mapped[int] = mapped_column(ForeignKey("calibrations.id"), index=True)
    outcome: Mapped[str] = mapped_column(String(16))
    explanation: Mapped[str] = mapped_column(String(250))
    segment_ids: Mapped[list] = mapped_column(JSON)
    input_sha256: Mapped[str] = mapped_column(String(64))
    fitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ReleaseSlot(Base):
    __tablename__ = "release_slots"
    __table_args__ = (
        UniqueConstraint("probe_id", "day", "mode", name="unique_active_light_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probe_id: Mapped[int] = mapped_column(ForeignKey("probes.id"))
    day: Mapped[date] = mapped_column(Date)
    mode: Mapped[str] = mapped_column(String(8))
    calibration_id: Mapped[int] = mapped_column(ForeignKey("calibrations.id"), unique=True)
