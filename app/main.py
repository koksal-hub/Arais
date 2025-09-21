from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.dashboard import router as dashboard_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.repo.database import init_db

configure_logging()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(dashboard_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    logger.info("starting up", environment=settings.environment)
    init_db()


@app.on_event("shutdown")
def shutdown_event() -> None:
    logger.info("shutting down")


__all__ = ["app"]
