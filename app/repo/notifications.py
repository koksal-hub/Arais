from __future__ import annotations

from typing import Iterable

from sqlmodel import select

from app.models.base import NotificationRule
from app.repo.database import session_scope


class NotificationRepository:
    def create_rule(
        self,
        *,
        channel_id: int,
        metric: str,
        threshold: float,
        direction: str,
        channel: str,
    ) -> NotificationRule:
        with session_scope() as session:
            rule = NotificationRule(
                channel_id=channel_id,
                metric=metric,
                threshold=threshold,
                direction=direction,
                channel=channel,
            )
            session.add(rule)
            session.flush()
            return rule

    def list_rules(self, channel_id: int) -> list[NotificationRule]:
        with session_scope() as session:
            statement = select(NotificationRule).where(NotificationRule.channel_id == channel_id)
            return list(session.exec(statement))


__all__ = ["NotificationRepository"]
