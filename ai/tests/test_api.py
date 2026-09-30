from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

GOOD_PAYLOAD = {
    "material": "steel",
    "shift": "day",
    "dimension_deviation_pct": 0.4,
    "surface_roughness_ra": 0.6,
    "torque_nm": 12.0,
    "temperature_c": 28.0,
    "vibration_mm_s": 0.9,
    "cycle_time_s": 12.0,
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_loaded_model(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"]


def test_predict_returns_a_severity(client: TestClient) -> None:
    response = client.post("/predict", json=GOOD_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] in {"minor", "major", "critical"}
    assert 0.0 <= body["confidence"] <= 1.0
    assert set(body["scores"]) == {"minor", "major", "critical"}


def test_predict_escalates_severity_for_bad_measurements(client: TestClient) -> None:
    severe = {
        **GOOD_PAYLOAD,
        "dimension_deviation_pct": 55.0,
        "surface_roughness_ra": 25.0,
        "torque_nm": 330.0,
        "vibration_mm_s": 45.0,
    }

    assert client.post("/predict", json=GOOD_PAYLOAD).json()["severity"] == "minor"
    assert client.post("/predict", json=severe).json()["severity"] == "critical"


def test_predict_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post("/predict", json={**GOOD_PAYLOAD, "unexpected": 1})

    assert response.status_code == 422


def test_predict_rejects_out_of_range_values(client: TestClient) -> None:
    response = client.post("/predict", json={**GOOD_PAYLOAD, "torque_nm": 5000})

    assert response.status_code == 422


def test_batch_predict_preserves_order(client: TestClient) -> None:
    response = client.post(
        "/predict/batch", json={"items": [GOOD_PAYLOAD, GOOD_PAYLOAD]}
    )

    assert response.status_code == 200
    predictions = response.json()["predictions"]
    assert len(predictions) == 2
    assert predictions[0]["severity"] == predictions[1]["severity"]


def test_batch_predict_rejects_empty_list(client: TestClient) -> None:
    assert client.post("/predict/batch", json={"items": []}).status_code == 422


def test_train_endpoint_retrains_model(client: TestClient) -> None:
    response = client.post("/train", json={"samples": 300, "seed": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["samples"] == 300
    assert body["accuracy"] > 0.5


def test_openapi_schema_is_served(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/predict" in schema["paths"]
    assert "/train" in schema["paths"]
