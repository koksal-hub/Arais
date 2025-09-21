from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.repo.comments import CommentRepository

logger = get_logger(__name__)


@dataclass(slots=True)
class CommentFilter:
    keyword: str | None = None
    flagged_only: bool = False


class CommentService:
    def __init__(self, repo: CommentRepository) -> None:
        self.repo = repo

    def ingest_comment(
        self,
        *,
        channel_id: int,
        video_id: str,
        author: str,
        text: str,
    ) -> dict[str, bool]:
        rules = self.repo.list_rules()
        flagged = False
        requires_approval = False
        queued_replies: list[int] = []

        for rule in rules:
            if re.search(rule.pattern, text, re.IGNORECASE):
                if rule.action == "flag":
                    flagged = True
                if rule.action == "auto_reply" and rule.template_ref:
                    requires_approval = True

        comment = self.repo.add_comment(
            channel_id=channel_id,
            video_id=video_id,
            author=author,
            text=text,
            flagged=flagged,
            requires_approval=requires_approval,
        )

        if requires_approval:
            for rule in rules:
                if rule.action == "auto_reply" and rule.template_ref and re.search(rule.pattern, text, re.IGNORECASE):
                    queue_item = self.repo.enqueue_reply(comment.id, rule.template_ref)
                    queued_replies.append(queue_item.id)
                    logger.info("auto reply enqueued", comment_id=comment.id, template=rule.template_ref)

        return {"flagged": flagged, "requires_approval": requires_approval, "queued_replies": bool(queued_replies)}

    def list_comments(self, channel_id: int, *, filter: CommentFilter | None = None) -> list[dict[str, str]]:
        comments = self.repo.list_comments(channel_id, flagged=filter.flagged_only if filter else None)
        results: list[dict[str, str]] = []
        for comment in comments:
            if filter and filter.keyword and filter.keyword.lower() not in comment.text.lower():
                continue
            results.append(
                {
                    "author": comment.author,
                    "text": comment.text,
                    "flagged": str(comment.flagged),
                    "requires_approval": str(comment.requires_approval),
                }
            )
        return results

    def approve_reply(self, queue_id: int) -> None:
        pending = self.repo.pending_replies()
        if not any(item.id == queue_id for item in pending):
            raise NotFoundError("Yanıt kuyruğu kaydı bulunamadı")
        self.repo.approve_reply(queue_id)
        logger.info("reply approved", queue_id=queue_id)

    def pending_replies(self) -> list[dict[str, str]]:
        items = self.repo.pending_replies()
        return [{"comment_id": str(item.comment_id), "template_ref": item.template_ref} for item in items]


__all__ = ["CommentService", "CommentFilter"]
