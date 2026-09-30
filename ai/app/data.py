"""Synthetic inspection data generation.

The severity label is derived from a deterministic scoring rule that encodes
domain knowledge, so the dataset is reproducible and the learned model has a
realisable signal to capture.
"""

from __future__ import annotations

import numpy as np

from .schemas import FEATURE_NAMES, Severity

SEVERITIES: tuple[Severity, ...] = ("minor", "major", "critical")

MATERIALS: tuple[str, ...] = ("steel", "aluminum", "plastic", "brass", "composite")
SHIFTS: tuple[str, ...] = ("day", "evening", "night")

# Upper bound considered "acceptable" for each numeric signal.
REFERENCE_LIMITS: dict[str, float] = {
    "dimension_deviation_pct": 5.0,
    "surface_roughness_ra": 3.2,
    "torque_nm": 45.0,
    "temperature_c": 95.0,
    "vibration_mm_s": 8.5,
    "cycle_time_s": 60.0,
}

WEIGHTS: dict[str, float] = {
    "dimension_deviation_pct": 0.30,
    "surface_roughness_ra": 0.20,
    "torque_nm": 0.20,
    "vibration_mm_s": 0.15,
    "temperature_c": 0.10,
    "cycle_time_s": 0.05,
}

SHIFT_PENALTY: dict[str, float] = {"day": 0.0, "evening": 0.02, "night": 0.05}

MAJOR_THRESHOLD = 0.42
CRITICAL_THRESHOLD = 0.58

# Share of rows where a single signal is pushed into the tail while the others
# stay nominal. Real inspection data is full of these one-sided excursions, and
# without them the model never sees the region where a lone severe measurement
# should still escalate the verdict.
OUTLIER_ROW_FRACTION = 0.25
OUTLIER_RATIO_RANGE = (0.6, 2.4)


def shift_index(shift: str) -> int:
    """Encode a shift as an integer column for the model matrix."""
    return SHIFTS.index(shift)


def severity_from_score(score: float) -> Severity:
    if score >= CRITICAL_THRESHOLD:
        return "critical"
    if score >= MAJOR_THRESHOLD:
        return "major"
    return "minor"


def risk_score(row: dict[str, float], shift: str) -> float:
    score = sum(
        WEIGHTS[name] * (row[name] / REFERENCE_LIMITS[name]) for name in FEATURE_NAMES
    )
    return score + SHIFT_PENALTY[shift]


def generate_dataset(
    samples: int = 1500, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(X, y, shift_labels)`` for a synthetic inspection dataset.

    Each numeric signal is drawn log-normally around 35% of its reference limit
    so most production parts pass comfortably, with a long upper tail producing
    genuine major and critical defects. A quarter of the rows have one signal
    deliberately pushed out of spec to cover one-sided excursions. Labels are
    derived from the measurements, so the signal is learnable but not degenerate.

    ``X`` has ``len(FEATURE_NAMES) + 1`` columns: the raw measurements followed
    by the integer-encoded shift.
    """
    rng = np.random.default_rng(seed)

    width = len(FEATURE_NAMES) + 1
    features = np.empty((samples, width), dtype=float)
    for column, name in enumerate(FEATURE_NAMES):
        limit = REFERENCE_LIMITS[name]
        ratio = np.exp(rng.normal(loc=np.log(0.35), scale=0.55, size=samples))
        features[:, column] = np.clip(ratio, 0.01, 2.4) * limit

    low, high = OUTLIER_RATIO_RANGE
    outlier_rows = rng.choice(
        samples, size=int(samples * OUTLIER_ROW_FRACTION), replace=False
    )
    for row_index in outlier_rows:
        column = int(rng.integers(0, len(FEATURE_NAMES)))
        name = FEATURE_NAMES[column]
        limit = REFERENCE_LIMITS[name]
        ratio = float(rng.uniform(low, high))
        features[row_index, column] = ratio * limit

    shift_labels = rng.choice(SHIFTS, size=samples, p=[0.5, 0.3, 0.2])
    features[:, -1] = [shift_index(str(shift)) for shift in shift_labels]

    labels = np.empty(samples, dtype=object)
    for row_index in range(samples):
        row = {
            name: float(features[row_index, column])
            for column, name in enumerate(FEATURE_NAMES)
        }
        labels[row_index] = severity_from_score(
            risk_score(row, str(shift_labels[row_index]))
        )

    return features, labels.astype(str), shift_labels.astype(str)


def to_records(
    features: np.ndarray, shifts: np.ndarray, materials: np.ndarray
) -> list[dict[str, object]]:
    """Flatten a numeric matrix into InspectionFeatures-compatible dicts."""
    records: list[dict[str, object]] = []
    for row_index, row in enumerate(features):
        record: dict[str, object] = {
            "material": materials[row_index],
            "shift": shifts[row_index],
        }
        for col, name in enumerate(FEATURE_NAMES):
            record[name] = round(float(row[col]), 4)
        records.append(record)
    return records
