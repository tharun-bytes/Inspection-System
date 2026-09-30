from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai_client import AIClient
from app.database import Base, get_db
from app.main import app
from app.routers.inspections import get_ai_client
from app.schemas import SeverityVerdict

TEST_DATABASE_URL = "sqlite://"


class StubAIClient(AIClient):
    """Deterministic stand-in for the real AI service.

    Severity is derived from dimension deviation so tests never need the model
    service to be running. Set ``stub.ai_available = False`` to simulate an
    outage.
    """

    def __init__(self) -> None:
        super().__init__(base_url="http://stub", timeout=1.0, enabled=True)
        self.ai_available = True
        self.calls: list[dict[str, object]] = []

    async def predict(
        self, payload: dict[str, object]
    ) -> tuple[SeverityVerdict | None, str | None]:
        self.calls.append(payload)
        if not self.ai_available:
            return None, "AI service unreachable: connection refused"

        deviation = float(payload["dimension_deviation_pct"])
        if deviation >= 8.0:
            severity = "critical"
        elif deviation >= 3.0:
            severity = "major"
        else:
            severity = "minor"

        return (
            SeverityVerdict(severity=severity, confidence=0.9, model_version="stub-1"),
            None,
        )

    async def health(self) -> str:
        return "up" if self.ai_available else "down"


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()

    def override_get_db() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        app.dependency_overrides.clear()


@pytest.fixture()
def stub_ai() -> StubAIClient:
    return StubAIClient()


@pytest.fixture()
def client(db_session: Session, stub_ai: StubAIClient) -> Iterator[TestClient]:
    def override_get_ai_client() -> AIClient:
        return stub_ai

    app.dependency_overrides[get_ai_client] = override_get_ai_client
    with TestClient(app) as test_client:
        yield test_client


def sample_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "part_serial": "SN-0001",
        "part_name": "Drive Shaft",
        "inspector": "alice",
        "material": "steel",
        "shift": "day",
        "dimension_deviation_pct": 1.2,
        "surface_roughness_ra": 0.8,
        "torque_nm": 20.0,
        "temperature_c": 35.0,
        "vibration_mm_s": 1.1,
        "cycle_time_s": 15.0,
    }
    payload.update(overrides)
    return payload
