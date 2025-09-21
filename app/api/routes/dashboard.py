from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.repo.analytics import AnalyticsRepository
from app.repo.credentials import CredentialsRepository
from app.services.analytics import AnalyticsService
from app.yt.mock_analytics import MockYouTubeAnalyticsClient

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/ui/templates")


def analytics_service() -> AnalyticsService:
    return AnalyticsService(
        analytics_repo=AnalyticsRepository(),
        credentials_repo=CredentialsRepository(),
        client=MockYouTubeAnalyticsClient(),
    )


@router.get("/{channel_id}", response_class=HTMLResponse)
def dashboard(request: Request, channel_id: int, service: AnalyticsService = Depends(analytics_service)):
    snapshot = service.latest_snapshot(channel_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")
    return templates.TemplateResponse("dashboard.html", {"request": request, "snapshot": snapshot, "channel_id": channel_id})


__all__ = ["router"]
