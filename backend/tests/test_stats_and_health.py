from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import sample_payload


def test_stats_are_zero_when_empty(client: TestClient) -> None:
    body = client.get("/api/inspections/stats").json()

    assert body["total_inspections"] == 0
    assert body["average_confidence"] is None
    assert body["severity_breakdown"] == []
    assert body["critical_rate"] == 0.0


def test_stats_aggregate_severity_and_status(client: TestClient) -> None:
    for index, deviation in enumerate([0.5, 4.0, 12.0, 0.5]):
        client.post(
            "/api/inspections",
            json=sample_payload(
                part_serial=f"SN-{index:04d}", dimension_deviation_pct=deviation
            ),
        )

    body = client.get("/api/inspections/stats").json()

    assert body["total_inspections"] == 4
    assert body["severity_breakdown"] == [
        {"severity": "critical", "count": 1},
        {"severity": "major", "count": 1},
        {"severity": "minor", "count": 2},
    ]
    assert body["status_breakdown"] == [
        {"status": "failed", "count": 1},
        {"status": "passed", "count": 2},
        {"status": "review", "count": 1},
    ]
    assert body["critical_rate"] == 0.25
    assert body["average_confidence"] == 0.9


def test_stats_exclude_unscored_records_from_critical_rate(
    client: TestClient, stub_ai
) -> None:
    stub_ai.ai_available = False
    for index in range(2):
        client.post(
            "/api/inspections",
            json=sample_payload(part_serial=f"SN-{index:04d}"),
        )

    body = client.get("/api/inspections/stats").json()

    assert body["total_inspections"] == 2
    assert body["status_breakdown"] == [{"status": "pending", "count": 2}]
    assert body["critical_rate"] == 0.0
    assert body["average_confidence"] is None


def test_health_reports_dependencies(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["database"] == "up"
    assert body["ai_service"] == "up"


def test_health_degrades_when_ai_is_down(client: TestClient, stub_ai) -> None:
    stub_ai.ai_available = False

    body = client.get("/health").json()

    assert body["ai_service"] == "down"
    assert body["status"] == "ok"


def test_root_advertises_docs(client: TestClient) -> None:
    body = client.get("/").json()

    assert body["docs"] == "/docs"


def test_openapi_exposes_expected_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/inspections" in paths
    assert "/api/inspections/stats" in paths
    assert "/health" in paths
