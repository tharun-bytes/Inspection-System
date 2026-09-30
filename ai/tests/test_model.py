from __future__ import annotations

import pytest

from app.data import SEVERITIES
from app.model import SeverityModel
from app.schemas import InspectionFeatures

PERFECT = InspectionFeatures(
    material="steel",
    shift="day",
    dimension_deviation_pct=0.05,
    surface_roughness_ra=0.1,
    torque_nm=5.0,
    temperature_c=20.0,
    vibration_mm_s=0.2,
    cycle_time_s=8.0,
)

BADLY_OUT_OF_SPEC = InspectionFeatures(
    material="composite",
    shift="night",
    dimension_deviation_pct=48.0,
    surface_roughness_ra=22.0,
    torque_nm=310.0,
    temperature_c=190.0,
    vibration_mm_s=41.0,
    cycle_time_s=430.0,
)


@pytest.fixture(scope="module")
def trained_model() -> SeverityModel:
    instance = SeverityModel()
    instance.train(samples=600, seed=11)
    return instance


def test_predict_before_training_raises(trained_model: SeverityModel) -> None:
    fresh = SeverityModel()
    assert fresh.is_loaded is False
    with pytest.raises(RuntimeError):
        fresh.predict(PERFECT)


def test_train_reports_all_classes(trained_model: SeverityModel) -> None:
    report = trained_model.train(samples=600, seed=5)

    assert trained_model.is_loaded is True
    assert report.samples == 600
    assert set(report.class_distribution) == set(SEVERITIES)
    assert sum(report.class_distribution.values()) == 600
    assert 0.0 <= report.accuracy <= 1.0
    assert 0.0 <= report.macro_f1 <= 1.0


def test_model_learns_the_severity_signal(trained_model: SeverityModel) -> None:
    clean = trained_model.predict(PERFECT)
    dirty = trained_model.predict(BADLY_OUT_OF_SPEC)

    assert clean.severity == "minor"
    assert dirty.severity == "critical"
    assert dirty.confidence > 0.6


def test_single_out_of_spec_measurement_still_escalates(
    trained_model: SeverityModel,
) -> None:
    """One bad signal among nominal ones must not be read as merely 'major'."""
    only_dimensional_outlier = trained_model.predict(
        InspectionFeatures(
            material="steel",
            shift="day",
            dimension_deviation_pct=11.0,
            surface_roughness_ra=0.4,
            torque_nm=10.0,
            temperature_c=25.0,
            vibration_mm_s=0.4,
            cycle_time_s=12.0,
        )
    )

    assert only_dimensional_outlier.severity == "critical"


def test_predictions_agree_with_the_documented_risk_rule(
    trained_model: SeverityModel,
) -> None:
    """The classifier should reproduce the additive rule it was trained on.

    Logistic regression in ratio space can express the rule's boundaries
    directly, so agreement is expected everywhere except within a hair of a
    threshold, where the decision is genuinely a coin flip.
    """
    from app.data import (
        CRITICAL_THRESHOLD,
        MAJOR_THRESHOLD,
        risk_score,
        severity_from_score,
    )

    margin = 0.06
    checked = 0

    for deviation in (0.4, 1.5, 2.0, 3.0, 5.0, 9.0, 12.0, 16.0, 20.0):
        features = InspectionFeatures(
            material="steel",
            shift="day",
            dimension_deviation_pct=deviation,
            surface_roughness_ra=0.4,
            torque_nm=10.0,
            temperature_c=25.0,
            vibration_mm_s=0.4,
            cycle_time_s=12.0,
        )
        score = risk_score(features.model_dump(), "day")
        if min(abs(score - MAJOR_THRESHOLD), abs(score - CRITICAL_THRESHOLD)) < margin:
            continue

        expected = severity_from_score(score)
        assert trained_model.predict(features).severity == expected, deviation
        checked += 1

    assert checked >= 6, "sweep should cover enough decisive cases"


def test_prediction_scores_sum_to_one(trained_model: SeverityModel) -> None:
    prediction = trained_model.predict(PERFECT)

    assert set(prediction.scores) == set(SEVERITIES)
    assert sum(prediction.scores.values()) == pytest.approx(1.0, abs=1e-3)
    assert prediction.model_version == trained_model.version


def test_persistence_roundtrip(trained_model: SeverityModel) -> None:
    trained_model.save()

    reloaded = SeverityModel()
    assert reloaded.load() is True
    assert reloaded.version == trained_model.version
    assert reloaded.predict(PERFECT).severity == trained_model.predict(PERFECT).severity


def test_load_without_artifact_returns_false(
    trained_model: SeverityModel, tmp_path, monkeypatch
) -> None:
    import app.model as model_module

    monkeypatch.setattr(model_module, "MODEL_PATH", tmp_path / "missing.joblib")
    assert SeverityModel().load() is False
