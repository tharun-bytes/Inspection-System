"""End-to-end checks against a running stack.

Run the whole system first, then:

    python -m pytest integration/tests -v

Set ``SKIP_E2E=1`` to skip (used by CI when no services are available).
"""

from __future__ import annotations

import os

import pytest
import requests

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_E2E") == "1", reason="SKIP_E2E=1"
)

AI_URL = os.getenv("E2E_AI_URL", "http://127.0.0.1:8001")
API_URL = os.getenv("E2E_API_URL", "http://127.0.0.1:8000")

TIMEOUT = 20


def payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "part_serial": "E2E-0001",
        "part_name": "Drive Shaft",
        "inspector": "e2e",
        "material": "steel",
        "shift": "day",
        "dimension_deviation_pct": 0.3,
        "surface_roughness_ra": 0.5,
        "torque_nm": 15.0,
        "temperature_c": 30.0,
        "vibration_mm_s": 0.8,
        "cycle_time_s": 14.0,
    }
    body.update(overrides)
    return body


@pytest.fixture(scope="session")
def session():
    http = requests.Session()
    yield http
    http.close()


def test_ai_service_is_up(session) -> None:
    body = session.get(f"{AI_URL}/health", timeout=TIMEOUT).json()

    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_backend_reports_both_dependencies_up(session) -> None:
    body = session.get(f"{API_URL}/health", timeout=TIMEOUT).json()

    assert body["database"] == "up"
    assert body["ai_service"] == "up"


def test_clean_inspection_passes(session) -> None:
    response = session.post(
        f"{API_URL}/api/inspections", json=payload(), timeout=TIMEOUT
    )
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["severity"] == "minor"
    assert body["status"] == "passed"
    assert body["ai_warning"] is None
    assert 0.0 <= body["confidence"] <= 1.0


def test_severe_inspection_fails(session) -> None:
    response = session.post(
        f"{API_URL}/api/inspections",
        json=payload(
            part_serial="E2E-0002",
            dimension_deviation_pct=12.0,
            surface_roughness_ra=18.0,
            torque_nm=280.0,
            vibration_mm_s=35.0,
            temperature_c=150.0,
        ),
        timeout=TIMEOUT,
    )
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["severity"] == "critical"
    assert body["status"] == "failed"


def test_duplicate_serial_conflicts(session) -> None:
    session.post(f"{API_URL}/api/inspections", json=payload(), timeout=TIMEOUT)
    second = session.post(
        f"{API_URL}/api/inspections", json=payload(), timeout=TIMEOUT
    )

    assert second.status_code == 409


def test_filtering_and_stats_agree(session) -> None:
    critical = session.get(
        f"{API_URL}/api/inspections", params={"severity": "critical"}, timeout=TIMEOUT
    ).json()
    stats = session.get(f"{API_URL}/api/inspections/stats", timeout=TIMEOUT).json()

    assert critical["total"] >= 1
    assert stats["total_inspections"] >= critical["total"]
    assert 0.0 <= stats["critical_rate"] <= 1.0
    assert stats["average_confidence"] is None or 0.0 <= stats["average_confidence"] <= 1.0


def test_reinspect_is_idempotent(session) -> None:
    created = session.post(
        f"{API_URL}/api/inspections", json=payload(part_serial="E2E-0003"), timeout=TIMEOUT
    ).json()
    again = session.post(
        f"{API_URL}/api/inspections/{created['id']}/reinspect", timeout=TIMEOUT
    ).json()

    assert again["severity"] == created["severity"]
    assert again["status"] == created["status"]


def test_invalid_payload_is_rejected(session) -> None:
    response = session.post(
        f"{API_URL}/api/inspections",
        json=payload(part_serial="E2E-0004", torque_nm=99_999),
        timeout=TIMEOUT,
    )

    assert response.status_code == 422


def test_delete_removes_the_record(session) -> None:
    created = session.post(
        f"{API_URL}/api/inspections", json=payload(part_serial="E2E-0005"), timeout=TIMEOUT
    ).json()

    assert session.delete(f"{API_URL}/api/inspections/{created['id']}", timeout=TIMEOUT).status_code == 204
    assert session.get(f"{API_URL}/api/inspections/{created['id']}", timeout=TIMEOUT).status_code == 404
