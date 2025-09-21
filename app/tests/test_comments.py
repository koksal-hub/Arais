from __future__ import annotations

from app.repo.comments import CommentRepository
from app.services.comments import CommentFilter, CommentService


def test_comment_ingestion_with_rules():
    repo = CommentRepository()
    service = CommentService(repo)
    repo.add_rule(pattern="buy now", action="flag")
    repo.add_rule(pattern="thanks", action="auto_reply", template_ref="thank_you")

    result = service.ingest_comment(
        channel_id=1,
        video_id="vid123",
        author="Ali",
        text="Buy now and thanks!",
    )
    assert result["flagged"] is True
    pending = service.pending_replies()
    assert pending[0]["template_ref"] == "thank_you"


def test_comment_filtering():
    repo = CommentRepository()
    service = CommentService(repo)
    repo.add_rule(pattern="spam", action="flag")
    service.ingest_comment(channel_id=1, video_id="v1", author="Ayşe", text="Harika video")
    service.ingest_comment(channel_id=1, video_id="v1", author="Mehmet", text="spam link")
    filtered = service.list_comments(1, filter=CommentFilter(keyword="harika"))
    assert len(filtered) == 1
    flagged = service.list_comments(1, filter=CommentFilter(flagged_only=True))
    assert len(flagged) == 1
