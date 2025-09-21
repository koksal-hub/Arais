from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from sqlmodel import select

from app.models.base import UploadJob, VideoPlan
from app.repo.database import session_scope


class VideoRepository:
    def create_plan(
        self,
        *,
        channel_id: int,
        title: str,
        description: str,
        tags: Sequence[str],
        schedule_at: datetime | None,
        status: str,
        category_id: str | None,
        video_path: str | None,
        thumbnail_path: str | None,
    ) -> VideoPlan:
        with session_scope() as session:
            plan = VideoPlan(
                channel_id=channel_id,
                title=title,
                description=description,
                tags=list(tags),
                schedule_at=schedule_at,
                status=status,
                category_id=category_id,
                video_path=video_path,
                thumbnail_path=thumbnail_path,
            )
            session.add(plan)
            session.flush()
            return plan

    def get_plan(self, plan_id: int) -> VideoPlan | None:
        with session_scope() as session:
            return session.get(VideoPlan, plan_id)

    def update_status(self, plan_id: int, status: str) -> None:
        with session_scope() as session:
            plan = session.get(VideoPlan, plan_id)
            if not plan:
                return
            plan.status = status
            session.add(plan)

    def create_upload_job(self, video_plan_id: int) -> UploadJob:
        with session_scope() as session:
            job = UploadJob(video_plan_id=video_plan_id)
            session.add(job)
            session.flush()
            return job

    def update_upload_job(
        self,
        job_id: int,
        *,
        state: str,
        result_ref: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with session_scope() as session:
            job = session.get(UploadJob, job_id)
            if not job:
                return
            job.state = state
            job.result_ref = result_ref
            job.error_message = error_message
            job.attempts += 1
            session.add(job)

    def get_due_plans(self, now: datetime) -> Iterable[VideoPlan]:
        with session_scope() as session:
            statement = select(VideoPlan).where(
                VideoPlan.schedule_at != None,  # noqa: E711
                VideoPlan.schedule_at <= now,
                VideoPlan.status == "scheduled",
            )
            return list(session.exec(statement))


__all__ = ["VideoRepository"]
