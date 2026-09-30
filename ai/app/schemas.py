from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["minor", "major", "critical"]
Material = Literal["steel", "aluminum", "plastic", "brass", "composite"]
Shift = Literal["day", "evening", "night"]

FEATURE_NAMES: tuple[str, ...] = (
    "dimension_deviation_pct",
    "surface_roughness_ra",
    "torque_nm",
    "temperature_c",
    "vibration_mm_s",
    "cycle_time_s",
)


class InspectionFeatures(BaseModel):
    """A single inspection measurement fed to the severity model."""

    model_config = ConfigDict(extra="forbid")

    material: Material = Field(default="steel")
    shift: Shift = Field(default="day")
    dimension_deviation_pct: float = Field(ge=0, le=100)
    surface_roughness_ra: float = Field(ge=0, le=50)
    torque_nm: float = Field(ge=0, le=400)
    temperature_c: float = Field(ge=-40, le=250)
    vibration_mm_s: float = Field(ge=0, le=60)
    cycle_time_s: float = Field(ge=0, le=600)


class Prediction(BaseModel):
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, float] = Field(
        description="Predicted probability per severity class."
    )
    model_version: str


class TrainRequest(BaseModel):
    samples: int = Field(default=1500, ge=200, le=50_000)
    seed: int = Field(default=42, ge=0)


class TrainResponse(BaseModel):
    model_version: str
    samples: int
    accuracy: float
    macro_f1: float
    trained_in_seconds: float
    class_distribution: dict[str, int]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: str | None
    version: str


class BatchPredictionRequest(BaseModel):
    items: list[InspectionFeatures] = Field(min_length=1, max_length=500)


class BatchPredictionResponse(BaseModel):
    predictions: list[Prediction]
