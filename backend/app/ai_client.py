"""HTTP client for the AI severity service.

The backend must stay usable when the AI service is down, so every failure is
returned as a warning alongside a ``None`` verdict instead of raising.
"""

from __future__ import annotations

import logging

import httpx

from .config import get_settings
from .schemas import SeverityVerdict

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    """Raised only when a caller explicitly wants strict behaviour."""


class AIClient:
    def __init__(self, base_url: str, timeout: float, enabled: bool = True) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def health(self) -> str:
        if not self._enabled:
            return "disabled"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/health")
            return "up" if response.status_code == 200 else "down"
        except httpx.HTTPError as exc:
            logger.warning("AI health check failed: %s", exc)
            return "down"

    async def predict(
        self, payload: dict[str, object]
    ) -> tuple[SeverityVerdict | None, str | None]:
        """Return ``(verdict, warning)``; exactly one of the two is not ``None``."""
        if not self._enabled:
            return None, "AI service is disabled"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/predict", json=payload
                )
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException:
            return None, f"AI service timed out after {self._timeout}s"
        except httpx.HTTPStatusError as exc:
            return None, f"AI service returned {exc.response.status_code}"
        except httpx.HTTPError as exc:
            return None, f"AI service unreachable: {exc}"
        except ValueError:
            return None, "AI service returned a malformed response"

        try:
            return (
                SeverityVerdict(
                    severity=body["severity"],
                    confidence=float(body["confidence"]),
                    model_version=body.get("model_version"),
                ),
                None,
            )
        except (KeyError, TypeError, ValueError):
            return None, "AI service response missing severity or confidence"


def build_ai_client() -> AIClient:
    settings = get_settings()
    return AIClient(
        base_url=settings.ai_service_url,
        timeout=settings.ai_timeout_seconds,
        enabled=settings.ai_enabled,
    )
