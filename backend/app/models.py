from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

Severity = Literal["minor", "major", "critical"]
RecordStatus = Literal["pending", "passed", "failed", "review"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_serial: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    part_name: Mapped[str] = mapped_column(String(128))
    inspector: Mapped[str] = mapped_column(String(64))

    material: Mapped[str] = mapped_column(String(32), default="steel")
    shift: Mapped[str] = mapped_column(String(16), default="day")

    dimension_deviation_pct: Mapped[float] = mapped_column(Float, default=0.0)
    surface_roughness_ra: Mapped[float] = mapped_column(Float, default=0.0)
    torque_nm: Mapped[float] = mapped_column(Float, default=0.0)
    temperature_c: Mapped[float] = mapped_column(Float, default=0.0)
    vibration_mm_s: Mapped[float] = mapped_column(Float, default=0.0)
    cycle_time_s: Mapped[float] = mapped_column(Float, default=0.0)

    severity: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    @property
    def measurement_payload(self) -> dict[str, object]:
        """The subset of fields the AI service expects."""
        return {
            "material": self.material,
            "shift": self.shift,
            "dimension_deviation_pct": self.dimension_deviation_pct,
            "surface_roughness_ra": self.surface_roughness_ra,
            "torque_nm": self.torque_nm,
            "temperature_c": self.temperature_c,
            "vibration_mm_s": self.vibration_mm_s,
            "cycle_time_s": self.cycle_time_s,
        }
