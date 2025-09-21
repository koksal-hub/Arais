from __future__ import annotations

from datetime import datetime
from typing import Sequence

from app.core.errors import AppException, NotFoundError
from app.core.logging import get_logger
from app.core.retry import retry
from app.repo.credentials import CredentialsRepository
from app.repo.videos import VideoRepository
from app.yt.upload_client import UploadResult, YouTubeUploadClient

logger = get_logger(__name__)


class VideoUploadService:
    def __init__(
        self,
        video_repo: VideoRepository,
        cred_repo: CredentialsRepository,
        client: YouTubeUploadClient,
    ) -> None:
        self.video_repo = video_repo
        self.cred_repo = cred_repo
        self.client = client

    def validate_metadata(
        self,
        *,
        title: str,
        description: str,
        tags: Sequence[str],
        category_id: str | None,
    ) -> None:
        if not title.strip():
            raise AppException("Başlık boş olamaz")
        if len(title) > 100:
            raise AppException("Başlık 100 karakterden uzun olamaz")
        if len(description) > 5000:
            raise AppException("Açıklama 5000 karakterden uzun olamaz")
        if len(tags) > 50:
            raise AppException("En fazla 50 etiket kullanılabilir")

    def create_plan(
        self,
        *,
        channel_id: int,
        title: str,
        description: str,
        tags: Sequence[str],
        schedule_at: datetime | None,
        category_id: str | None,
        video_path: str | None,
        thumbnail_path: str | None,
    ) -> int:
        self.validate_metadata(title=title, description=description, tags=tags, category_id=category_id)
        status = "draft" if schedule_at is None else "scheduled"
        plan = self.video_repo.create_plan(
            channel_id=channel_id,
            title=title,
            description=description,
            tags=tags,
            schedule_at=schedule_at,
            status=status,
            category_id=category_id,
            video_path=video_path,
            thumbnail_path=thumbnail_path,
        )
        logger.info("video plan created", plan_id=plan.id, channel_id=channel_id, status=status)
        return plan.id

    def schedule_plan(self, plan_id: int, schedule_at: datetime) -> None:
        plan = self.video_repo.get_plan(plan_id)
        if not plan:
            raise NotFoundError("Video planı bulunamadı")
        plan.schedule_at = schedule_at
        plan.status = "scheduled"
        self.video_repo.update_status(plan_id, "scheduled")
        logger.info("video scheduled", plan_id=plan_id, schedule_at=schedule_at.isoformat())

    def _perform_upload(self, plan_id: int, *, dry_run: bool) -> UploadResult:
        plan = self.video_repo.get_plan(plan_id)
        if not plan:
            raise NotFoundError("Video planı bulunamadı")
        if not plan.video_path:
            raise AppException("Video dosyası tanımlı değil")

        credentials = self.cred_repo.get_credentials(plan.channel_id)
        if not credentials:
            raise AppException("Kanal yetkilendirmesi eksik")

        def operation() -> UploadResult:
            return self.client.upload(
                title=plan.title,
                description=plan.description,
                tags=list(plan.tags),
                category_id=plan.category_id,
                video_path=plan.video_path or "",
                thumbnail_path=plan.thumbnail_path,
                publish_at=plan.schedule_at,
                privacy_status="private" if dry_run else "public",
                dry_run=dry_run,
            )

        return retry(operation, retries=2, sleep_func=lambda _: None)

    def run_upload_job(self, plan_id: int, *, dry_run: bool = False) -> UploadResult:
        job = self.video_repo.create_upload_job(plan_id)
        try:
            result = self._perform_upload(plan_id, dry_run=dry_run)
            state = "completed" if not dry_run else "validated"
            self.video_repo.update_upload_job(job.id, state=state, result_ref=result.video_id)
            self.video_repo.update_status(plan_id, "published" if not dry_run else "validated")
            logger.info("upload job finished", job_id=job.id, state=state)
            return result
        except Exception as exc:
            self.video_repo.update_upload_job(job.id, state="failed", error_message=str(exc))
            logger.error("upload failed", job_id=job.id, error=str(exc))
            raise


__all__ = ["VideoUploadService"]
