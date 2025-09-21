from __future__ import annotations

from typing import Iterable, Sequence

from sqlmodel import select

from app.models.base import Comment, CommentReplyQueue, CommentRule
from app.repo.database import session_scope


class CommentRepository:
    def add_comment(
        self,
        *,
        channel_id: int,
        video_id: str,
        author: str,
        text: str,
        flagged: bool = False,
        requires_approval: bool = False,
    ) -> Comment:
        with session_scope() as session:
            comment = Comment(
                channel_id=channel_id,
                video_id=video_id,
                author=author,
                text=text,
                flagged=flagged,
                requires_approval=requires_approval,
            )
            session.add(comment)
            session.flush()
            return comment

    def list_comments(self, channel_id: int, *, flagged: bool | None = None) -> list[Comment]:
        with session_scope() as session:
            statement = select(Comment).where(Comment.channel_id == channel_id)
            if flagged is not None:
                statement = statement.where(Comment.flagged == flagged)
            return list(session.exec(statement))

    def add_rule(self, pattern: str, action: str, template_ref: str | None = None) -> CommentRule:
        with session_scope() as session:
            rule = CommentRule(pattern=pattern, action=action, template_ref=template_ref)
            session.add(rule)
            session.flush()
            return rule

    def list_rules(self) -> list[CommentRule]:
        with session_scope() as session:
            statement = select(CommentRule)
            return list(session.exec(statement))

    def enqueue_reply(self, comment_id: int, template_ref: str) -> CommentReplyQueue:
        with session_scope() as session:
            queue_item = CommentReplyQueue(comment_id=comment_id, template_ref=template_ref)
            session.add(queue_item)
            session.flush()
            return queue_item

    def approve_reply(self, queue_id: int) -> None:
        with session_scope() as session:
            item = session.get(CommentReplyQueue, queue_id)
            if not item:
                return
            item.approved = True
            session.add(item)

    def pending_replies(self) -> list[CommentReplyQueue]:
        with session_scope() as session:
            statement = select(CommentReplyQueue).where(CommentReplyQueue.approved.is_(False))
            return list(session.exec(statement))


__all__ = ["CommentRepository"]
