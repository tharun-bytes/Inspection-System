from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..ai_client import AIClient
from ..config import get_settings
from ..database import get_db
from ..routers.inspections import get_ai_client
from ..schemas import HealthResponse

router = APIRouter(tags=["ops"])


@router.get("/health", response_model=HealthResponse)
async def health(
    db: Session = Depends(get_db),
    client: AIClient = Depends(get_ai_client),
) -> HealthResponse:
    settings = get_settings()

    database: str
    try:
        db.execute(text("SELECT 1"))
        database = "up"
    except Exception:  # noqa: BLE001 - any driver error means the DB is unusable
        database = "down"

    ai_state = await client.health()

    return HealthResponse(
        status="ok" if database == "up" else "degraded",
        database=database,
        ai_service=ai_state,  # type: ignore[arg-type]
        version=settings.version,
    )
