from __future__ import annotations

from app.repo.crosspost import CrosspostRepository
from app.services.crosspost import CrosspostService


def test_crosspost_queue_and_complete():
    repo = CrosspostRepository()
    service = CrosspostService(repo)
    task_id = service.queue_post(1, "tiktok", {"caption": "Kısa video"})
    pending = service.pending_tasks()
    assert pending[0]["platform"] == "tiktok"
    service.complete_task(task_id)
    assert service.pending_tasks() == []
