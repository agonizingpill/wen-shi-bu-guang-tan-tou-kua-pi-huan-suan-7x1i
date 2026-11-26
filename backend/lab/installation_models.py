from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Probe(Base):
    __tablename__ = "probes"
    __table_args__ = (
        CheckConstraint("mount_cm BETWEEN 15 AND 300", name="valid_mount_cm"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True)
    bay: Mapped[str] = mapped_column(String(40))
    batch: Mapped[str] = mapped_column(String(30))
    reference_serial: Mapped[str] = mapped_column(String(32))
    mount_cm: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
