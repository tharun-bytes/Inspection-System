from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from .conftest import sample_payload


def test_create_inspection_persists_record(client: TestClient) -> None:
    response = client.post("/api/inspections", json=sample_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["part_serial"] == "SN-0001"
    assert body["status"] == "passed"
    assert body["ai_warning"] is None


def test_create_sends_measurements_to_ai(client: TestClient, stub_ai) -> None:
    client.post("/api/inspections", json=sample_payload())

    assert len(stub_ai.calls) == 1
    sent = stub_ai.calls[0]
    assert sent["material"] == "steel"
    assert sent["shift"] == "day"
    assert sent["dimension_deviation_pct"] == 1.2
    assert "part_serial" not in sent


@pytest.mark.parametrize(
    ("deviation", "expected_severity", "expected_status"),
    [
        (0.5, "minor", "passed"),
        (4.0, "major", "review"),
        (12.0, "critical", "failed"),
    ],
)
def test_status_is_derived_from_severity(
    client: TestClient, deviation: float, expected_severity: str, expected_status: str
) -> None:
    response = client.post(
        "/api/inspections",
        json=sample_payload(
            part_serial=f"SN-{deviation}", dimension_deviation_pct=deviation
        ),
    )

    body = response.json()
    assert body["severity"] == expected_severity
    assert body["status"] == expected_status
    assert body["ai_verdict"]["severity"] == expected_severity


def test_duplicate_serial_is_rejected(client: TestClient) -> None:
    client.post("/api/inspections", json=sample_payload())
    response = client.post("/api/inspections", json=sample_payload())

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_survives_ai_outage(client: TestClient, stub_ai) -> None:
    stub_ai.ai_available = False

    response = client.post("/api/inspections", json=sample_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["severity"] is None
    assert "unreachable" in body["ai_warning"]


def test_reinspect_backfills_verdict_after_outage(
    client: TestClient, stub_ai
) -> None:
    stub_ai.ai_available = False
    created = client.post("/api/inspections", json=sample_payload()).json()

    stub_ai.ai_available = True
    response = client.post(f"/api/inspections/{created['id']}/reinspect")

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "minor"
    assert body["status"] == "passed"
    assert body["ai_warning"] is None


def test_create_rejects_unknown_field(client: TestClient) -> None:
    response = client.post(
        "/api/inspections", json=sample_payload(unexpected="value")
    )

    assert response.status_code == 422


def test_create_rejects_out_of_range_measurement(client: TestClient) -> None:
    response = client.post("/api/inspections", json=sample_payload(torque_nm=9999))

    assert response.status_code == 422


def test_create_rejects_blank_part_serial(client: TestClient) -> None:
    response = client.post("/api/inspections", json=sample_payload(part_serial="   "))

    assert response.status_code == 422
