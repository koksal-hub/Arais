from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="", tags=["health"])


@router.get("/healthz", summary="Sağlık kontrolü")
def healthcheck() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "environment": settings.environment, "locale": settings.default_locale}


__all__ = ["router"]
