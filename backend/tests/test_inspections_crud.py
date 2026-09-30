from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import sample_payload


def _seed(client: TestClient, deviations: list[float] | None = None) -> None:
    """Seed one inspection per deviation value (minor < 3, major < 8, else critical)."""
    for index, deviation in enumerate(deviations or [0.5] * 3):
        client.post(
            "/api/inspections",
            json=sample_payload(
                part_serial=f"SN-{index:04d}", dimension_deviation_pct=deviation
            ),
        )


def test_list_is_empty_initially(client: TestClient) -> None:
    body = client.get("/api/inspections").json()

    assert body == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_returns_created_records(client: TestClient) -> None:
    _seed(client, [0.5, 4.0, 12.0])
    body = client.get("/api/inspections").json()

    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_pagination_slices_results(client: TestClient) -> None:
    _seed(client, [0.5, 0.5, 4.0, 4.0, 12.0])

    page = client.get("/api/inspections", params={"limit": 2, "offset": 0}).json()
    second = client.get("/api/inspections", params={"limit": 2, "offset": 2}).json()

    assert page["total"] == 5
    assert len(page["items"]) == 2
    assert len(second["items"]) == 2
    assert page["items"][0]["id"] != second["items"][0]["id"]


def test_filter_by_status(client: TestClient) -> None:
    _seed(client, [0.5, 4.0, 12.0])
    body = client.get("/api/inspections", params={"status": "failed"}).json()

    assert body["total"] == 1
    assert body["items"][0]["status"] == "failed"


def test_filter_by_severity(client: TestClient) -> None:
    _seed(client, [0.5, 4.0, 12.0])
    body = client.get("/api/inspections", params={"severity": "major"}).json()

    assert body["total"] == 1
    assert body["items"][0]["severity"] == "major"


def test_rejects_invalid_filter_value(client: TestClient) -> None:
    assert client.get("/api/inspections", params={"status": "bogus"}).status_code == 422
    assert client.get("/api/inspections", params={"severity": "fatal"}).status_code == 422


def test_rejects_out_of_range_pagination(client: TestClient) -> None:
    assert client.get("/api/inspections", params={"limit": 0}).status_code == 422
    assert client.get("/api/inspections", params={"limit": 999}).status_code == 422
    assert client.get("/api/inspections", params={"offset": -1}).status_code == 422


def test_get_single_inspection(client: TestClient) -> None:
    created = client.post("/api/inspections", json=sample_payload()).json()

    response = client.get(f"/api/inspections/{created['id']}")

    assert response.status_code == 200
    assert response.json()["part_serial"] == "SN-0001"


def test_get_missing_inspection_returns_404(client: TestClient) -> None:
    assert client.get("/api/inspections/424242").status_code == 404


def test_update_changes_fields(client: TestClient) -> None:
    created = client.post("/api/inspections", json=sample_payload()).json()

    response = client.patch(
        f"/api/inspections/{created['id']}",
        json={"status": "review", "notes": "Machine recalibrated"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "review"
    assert body["notes"] == "Machine recalibrated"


def test_update_leaves_unset_fields_untouched(client: TestClient) -> None:
    created = client.post("/api/inspections", json=sample_payload()).json()

    response = client.patch(f"/api/inspections/{created['id']}", json={"notes": "ok"})

    assert response.json()["part_name"] == "Drive Shaft"


def test_update_rejects_unknown_field(client: TestClient) -> None:
    created = client.post("/api/inspections", json=sample_payload()).json()

    response = client.patch(
        f"/api/inspections/{created['id']}", json={"severity": "critical"}
    )

    assert response.status_code == 422


def test_update_missing_inspection_returns_404(client: TestClient) -> None:
    assert client.patch("/api/inspections/999", json={"notes": "x"}).status_code == 404


def test_delete_removes_record(client: TestClient) -> None:
    created = client.post("/api/inspections", json=sample_payload()).json()

    deleted = client.delete(f"/api/inspections/{created['id']}")

    assert deleted.status_code == 204
    assert client.get(f"/api/inspections/{created['id']}").status_code == 404
    assert client.get("/api/inspections").json()["total"] == 0


def test_delete_missing_inspection_returns_404(client: TestClient) -> None:
    assert client.delete("/api/inspections/999").status_code == 404
