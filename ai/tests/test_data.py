from __future__ import annotations

import numpy as np
import pytest

from app.data import (
    CRITICAL_THRESHOLD,
    MAJOR_THRESHOLD,
    REFERENCE_LIMITS,
    SEVERITIES,
    SHIFTS,
    generate_dataset,
    risk_score,
    severity_from_score,
    shift_index,
    to_records,
)
from app.schemas import FEATURE_NAMES


def test_reference_limits_cover_every_feature() -> None:
    assert set(REFERENCE_LIMITS) == set(FEATURE_NAMES)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "minor"),
        (MAJOR_THRESHOLD - 0.01, "minor"),
        (MAJOR_THRESHOLD, "major"),
        (CRITICAL_THRESHOLD - 0.01, "major"),
        (CRITICAL_THRESHOLD, "critical"),
        (2.5, "critical"),
    ],
)
def test_severity_thresholds(score: float, expected: str) -> None:
    assert severity_from_score(score) == expected


def test_risk_score_is_monotonic_in_each_signal() -> None:
    baseline = {name: 0.0 for name in FEATURE_NAMES}
    baseline_score = risk_score(baseline, "day")

    for name in FEATURE_NAMES:
        worse = dict(baseline)
        worse[name] = REFERENCE_LIMITS[name]
        assert risk_score(worse, "day") > baseline_score


def test_night_shift_is_penalised_more_than_day() -> None:
    row = {name: 0.0 for name in FEATURE_NAMES}
    assert risk_score(row, "night") > risk_score(row, "evening") > risk_score(
        row, "day"
    )


def test_generate_dataset_shapes_and_labels() -> None:
    features, labels, shifts = generate_dataset(samples=300, seed=7)

    assert features.shape == (300, len(FEATURE_NAMES) + 1)
    assert labels.shape == (300,)
    assert shifts.shape == (300,)
    assert set(labels) <= set(SEVERITIES)
    assert np.all(features >= 0)


def test_shift_column_encodes_the_shift_label() -> None:
    features, _, shifts = generate_dataset(samples=200, seed=5)

    assert set(features[:, -1].astype(int)) <= set(range(len(SHIFTS)))
    for row_index in range(200):
        assert int(features[row_index, -1]) == SHIFTS.index(shifts[row_index])


def test_shift_index_is_stable() -> None:
    assert [shift_index(shift) for shift in SHIFTS] == list(range(len(SHIFTS)))


def test_generate_dataset_is_deterministic_for_a_seed() -> None:
    first, first_labels, _ = generate_dataset(samples=200, seed=3)
    second, second_labels, _ = generate_dataset(samples=200, seed=3)

    assert np.array_equal(first, second)
    assert np.array_equal(first_labels, second_labels)


def test_to_records_emits_every_feature_key() -> None:
    features, _, _ = generate_dataset(samples=10, seed=1)
    materials = np.array(["steel"] * 10)
    shifts = np.array(["day"] * 10)

    records = to_records(features, shifts, materials)

    assert len(records) == 10
    for record in records:
        assert set(record) == {"material", "shift", *FEATURE_NAMES}
        assert all(isinstance(record[name], float) for name in FEATURE_NAMES)
