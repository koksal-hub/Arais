from __future__ import annotations

from typing import Iterable

from sqlmodel import select

from app.models.base import CrosspostTask
from app.repo.database import session_scope


class CrosspostRepository:
    def create_task(self, video_plan_id: int, platform: str, payload: dict) -> CrosspostTask:
        with session_scope() as session:
            task = CrosspostTask(video_plan_id=video_plan_id, platform=platform, payload=payload)
            session.add(task)
            session.flush()
            return task

    def update_state(self, task_id: int, state: str) -> None:
        with session_scope() as session:
            task = session.get(CrosspostTask, task_id)
            if task:
                task.state = state
                session.add(task)

    def list_pending(self) -> list[CrosspostTask]:
        with session_scope() as session:
            statement = select(CrosspostTask).where(CrosspostTask.state == "pending")
            return list(session.exec(statement))


__all__ = ["CrosspostRepository"]
