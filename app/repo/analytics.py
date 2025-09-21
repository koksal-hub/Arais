from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from app.models.base import AnalyticsSnapshot
from app.repo.database import session_scope


class AnalyticsRepository:
    def save_snapshot(
        self,
        *,
        channel_id: int,
        views: int,
        watch_time: float,
        subs: int,
        ctr: float,
        top_videos: list[str],
        captured_at: datetime | None = None,
    ) -> AnalyticsSnapshot:
        with session_scope() as session:
            snapshot = AnalyticsSnapshot(
                channel_id=channel_id,
                views=views,
                watch_time=watch_time,
                subs=subs,
                ctr=ctr,
                top_videos=top_videos,
                captured_at=captured_at or datetime.utcnow(),
            )
            session.add(snapshot)
            session.flush()
            return snapshot

    def latest_snapshot(self, channel_id: int) -> AnalyticsSnapshot | None:
        with session_scope() as session:
            statement = select(AnalyticsSnapshot).where(AnalyticsSnapshot.channel_id == channel_id).order_by(AnalyticsSnapshot.captured_at.desc())
            return session.exec(statement).first()


__all__ = ["AnalyticsRepository"]
