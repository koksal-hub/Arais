from __future__ import annotations

from app.repo.crosspost import CrosspostRepository


class CrosspostService:
    def __init__(self, repo: CrosspostRepository) -> None:
        self.repo = repo

    def queue_post(self, video_plan_id: int, platform: str, payload: dict) -> int:
        task = self.repo.create_task(video_plan_id, platform, payload)
        return task.id

    def complete_task(self, task_id: int) -> None:
        self.repo.update_state(task_id, "completed")

    def pending_tasks(self) -> list[dict[str, str]]:
        tasks = self.repo.list_pending()
        return [{"platform": t.platform, "video_plan_id": str(t.video_plan_id)} for t in tasks]


__all__ = ["CrosspostService"]
