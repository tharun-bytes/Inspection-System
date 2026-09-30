from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Severity = Literal["minor", "major", "critical"]
RecordStatus = Literal["pending", "passed", "failed", "review"]

MAX_SERIAL_LENGTH = 64
MAX_PART_NAME_LENGTH = 128


def _validate_text(value: str, field: str, limit: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must not be empty")
    if len(cleaned) > limit:
        raise ValueError(f"{field} must be at most {limit} characters")
    return cleaned


class InspectionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_serial: str = Field(max_length=MAX_SERIAL_LENGTH)
    part_name: str = Field(max_length=MAX_PART_NAME_LENGTH)
    inspector: str = Field(max_length=MAX_SERIAL_LENGTH)
    material: Literal["steel", "aluminum", "plastic", "brass", "composite"] = "steel"
    shift: Literal["day", "evening", "night"] = "day"
    dimension_deviation_pct: float = Field(ge=0, le=100)
    surface_roughness_ra: float = Field(ge=0, le=50)
    torque_nm: float = Field(ge=0, le=400)
    temperature_c: float = Field(ge=-40, le=250)
    vibration_mm_s: float = Field(ge=0, le=60)
    cycle_time_s: float = Field(ge=0, le=600)
    notes: str | None = None

    @field_validator("part_serial", "part_name", "inspector")
    @classmethod
    def _clean_identifiers(cls, value: str, info) -> str:
        limits = {
            "part_serial": MAX_SERIAL_LENGTH,
            "part_name": MAX_PART_NAME_LENGTH,
            "inspector": MAX_SERIAL_LENGTH,
        }
        return _validate_text(value, info.field_name, limits[info.field_name])


class InspectionCreate(InspectionBase):
    pass


class InspectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_name: str | None = Field(default=None, max_length=MAX_PART_NAME_LENGTH)
    inspector: str | None = Field(default=None, max_length=MAX_SERIAL_LENGTH)
    material: Literal["steel", "aluminum", "plastic", "brass", "composite"] | None = None
    shift: Literal["day", "evening", "night"] | None = None
    dimension_deviation_pct: float | None = Field(default=None, ge=0, le=100)
    surface_roughness_ra: float | None = Field(default=None, ge=0, le=50)
    torque_nm: float | None = Field(default=None, ge=0, le=400)
    temperature_c: float | None = Field(default=None, ge=-40, le=250)
    vibration_mm_s: float | None = Field(default=None, ge=0, le=60)
    cycle_time_s: float | None = Field(default=None, ge=0, le=600)
    status: RecordStatus | None = None
    notes: str | None = None

    @field_validator("part_name", "inspector")
    @classmethod
    def _clean_optional(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        limits = {"part_name": MAX_PART_NAME_LENGTH, "inspector": MAX_SERIAL_LENGTH}
        return _validate_text(value, info.field_name, limits[info.field_name])


class InspectionRead(InspectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    severity: Severity | None
    confidence: float | None
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class SeverityVerdict(BaseModel):
    severity: Severity
    confidence: float
    model_version: str | None = None


class InspectionWithVerdict(InspectionRead):
    ai_verdict: SeverityVerdict | None = None
    ai_warning: str | None = None


class InspectionPage(BaseModel):
    items: list[InspectionRead]
    total: int
    limit: int
    offset: int


class SeverityCount(BaseModel):
    severity: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardStats(BaseModel):
    total_inspections: int
    average_confidence: float | None
    severity_breakdown: list[SeverityCount]
    status_breakdown: list[StatusCount]
    critical_rate: float


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["up", "down"]
    ai_service: Literal["up", "down", "disabled"]
    version: str
