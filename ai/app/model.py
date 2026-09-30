"""Severity model: training, persistence and inference."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import (
    REFERENCE_LIMITS,
    SEVERITIES,
    SHIFT_PENALTY,
    SHIFTS,
    generate_dataset,
    shift_index,
)
from .schemas import FEATURE_NAMES, InspectionFeatures, Prediction

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "severity_model.joblib"
METADATA_PATH = ARTIFACT_DIR / "model_metadata.json"

RANDOM_STATE = 42
_LIMITS = np.array([REFERENCE_LIMITS[name] for name in FEATURE_NAMES], dtype=float)
_PENALTIES = np.array([SHIFT_PENALTY[shift] for shift in SHIFTS], dtype=float)


class InspectionFeatureBuilder(BaseEstimator, TransformerMixin):
    """Turn raw measurements into ratios against their reference limits.

    Feeding the forest normalised ratios (plus the shift penalty) rather than raw
    physical units lets it learn the additive risk rule directly, which is what
    makes it correct for rare combinations such as one wildly out-of-spec
    measurement surrounded by nominal ones.
    """

    def fit(
        self, X: np.ndarray, y: np.ndarray | None = None
    ) -> InspectionFeatureBuilder:
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        matrix = np.asarray(X, dtype=float)
        ratios = matrix[:, : len(FEATURE_NAMES)] / _LIMITS
        codes = matrix[:, len(FEATURE_NAMES)].astype(int)
        codes = np.clip(codes, 0, len(_PENALTIES) - 1)
        return np.hstack([ratios, _PENALTIES[codes].reshape(-1, 1)])


@dataclass(frozen=True)
class TrainingReport:
    model_version: str
    samples: int
    accuracy: float
    macro_f1: float
    trained_in_seconds: float
    class_distribution: dict[str, int]


def _build_pipeline() -> Pipeline:
    """Build the severity pipeline.

    A regularised multinomial logistic regression is used rather than a tree
    ensemble on purpose. Once the measurements are expressed as ratios against
    their reference limits, severity is a *linear* function of those ratios, so
    linear decision boundaries are the correct inductive bias. Axis-aligned
    splits (as used by random forests) have to approximate a diagonal boundary
    with many small rectangles, which leaves the model unstable near the
    thresholds and prone to under-calling a lone severe measurement.
    """
    return Pipeline(
        [
            ("features", InspectionFeatureBuilder()),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=10.0,
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


class SeverityModel:
    """Thin wrapper that owns the fitted pipeline and its metadata."""

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._version: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    @property
    def version(self) -> str | None:
        return self._version

    @staticmethod
    def to_vector(features: InspectionFeatures) -> np.ndarray:
        """Build the raw model row: measurements plus the encoded shift."""
        row = [float(getattr(features, name)) for name in FEATURE_NAMES]
        row.append(float(shift_index(features.shift)))
        return np.array([row], dtype=float)

    def predict(self, features: InspectionFeatures) -> Prediction:
        if self._pipeline is None:
            raise RuntimeError("Model is not loaded. Call train() or load() first.")

        vector = self.to_vector(features)
        probabilities = self._pipeline.predict_proba(vector)[0]
        classes = self._pipeline.named_steps["classifier"].classes_

        best_index = int(np.argmax(probabilities))
        scores = {
            str(label): round(float(probabilities[index]), 6)
            for index, label in enumerate(classes)
        }

        return Prediction(
            severity=str(classes[best_index]),
            confidence=round(float(probabilities[best_index]), 6),
            scores=scores,
            model_version=self._version or "unknown",
        )

    def train(self, samples: int = 1500, seed: int = 42) -> TrainingReport:
        started = time.perf_counter()
        features, labels, _ = generate_dataset(samples=samples, seed=seed)

        x_train, x_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=seed, stratify=labels
        )

        pipeline = _build_pipeline()
        pipeline.fit(x_train, y_train)

        predictions = pipeline.predict(x_test)
        accuracy = accuracy_score(y_test, predictions)
        macro_f1 = f1_score(y_test, predictions, average="macro", zero_division=0)

        self._pipeline = pipeline
        self._version = f"{seed}-{uuid.uuid4().hex[:8]}"

        distribution = {
            label: int(np.sum(labels == label)) for label in SEVERITIES
        }
        elapsed = round(time.perf_counter() - started, 3)

        self.save()

        return TrainingReport(
            model_version=self._version,
            samples=samples,
            accuracy=round(float(accuracy), 4),
            macro_f1=round(float(macro_f1), 4),
            trained_in_seconds=elapsed,
            class_distribution=distribution,
        )

    def save(self) -> None:
        if self._pipeline is None:
            raise RuntimeError("Nothing to save: model is not trained.")
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"pipeline": self._pipeline, "version": self._version}, MODEL_PATH
        )
        METADATA_PATH.write_text(
            json.dumps(
                {
                    "model_version": self._version,
                    "features": list(FEATURE_NAMES),
                    "shift_encoding": {shift: i for i, shift in enumerate(SHIFTS)},
                    "classes": list(SEVERITIES),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> bool:
        """Load a persisted model. Returns False when no artifact exists."""
        if not MODEL_PATH.exists():
            return False
        payload = joblib.load(MODEL_PATH)
        self._pipeline = payload["pipeline"]
        self._version = payload["version"]
        return True


model = SeverityModel()
