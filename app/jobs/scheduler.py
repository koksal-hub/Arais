from __future__ import annotations

from datetime import datetime
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logging import get_logger
from app.repo.videos import VideoRepository
from app.services.video import VideoUploadService

logger = get_logger(__name__)


class PlanScheduler:
    def __init__(
        self,
        video_repo: VideoRepository,
        video_service: VideoUploadService,
        *,
        scheduler: BackgroundScheduler | None = None,
    ) -> None:
        self.video_repo = video_repo
        self.video_service = video_service
        self.scheduler = scheduler or BackgroundScheduler()

    def start(self) -> None:
        logger.info("scheduler starting")
        self.scheduler.add_job(self.process_due_plans, "interval", minutes=1, id="video-plan-processor")
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("scheduler stopped")

    def process_due_plans(self) -> list[int]:
        now = datetime.utcnow()
        due_plans = self.video_repo.get_due_plans(now)
        processed: list[int] = []
        for plan in due_plans:
            try:
                self.video_service.run_upload_job(plan.id, dry_run=False)
                processed.append(plan.id)
            except Exception as exc:  # pragma: no cover - log and continue
                logger.error("scheduled upload failed", plan_id=plan.id, error=str(exc))
        return processed


__all__ = ["PlanScheduler"]
