from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ConversionReceipt(Base):
    __tablename__ = "conversion_receipts"
    __table_args__ = (
        UniqueConstraint("probe_id", "day", "mode", "minute", name="unique_reading_minute"),
        CheckConstraint("minute BETWEEN 0 AND 1439 AND raw_lux >= 0 AND adjusted_lux >= 0",
                        name="valid_converted_reading"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probe_id: Mapped[int] = mapped_column(ForeignKey("probes.id"))
    calibration_id: Mapped[int] = mapped_column(ForeignKey("calibrations.id"))
    day: Mapped[date] = mapped_column(Date)
    mode: Mapped[str] = mapped_column(String(8))
    minute: Mapped[int] = mapped_column(Integer)
    raw_lux: Mapped[float] = mapped_column(Float)
    adjusted_lux: Mapped[float] = mapped_column(Float)
    entered_by: Mapped[str] = mapped_column(String(32))
