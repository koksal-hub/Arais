from __future__ import annotations

from datetime import datetime

from app.core.logging import get_logger
from app.repo.analytics import AnalyticsRepository
from app.repo.credentials import CredentialsRepository
from app.yt.analytics_client import AnalyticsResult, YouTubeAnalyticsClient

logger = get_logger(__name__)


class AnalyticsService:
    def __init__(
        self,
        *,
        analytics_repo: AnalyticsRepository,
        credentials_repo: CredentialsRepository,
        client: YouTubeAnalyticsClient,
    ) -> None:
        self.analytics_repo = analytics_repo
        self.credentials_repo = credentials_repo
        self.client = client

    def collect_snapshot(self, channel_id: int) -> AnalyticsResult:
        channel = self.credentials_repo.get_channel(channel_id)
        if not channel:
            raise ValueError("Kanal bulunamadı")
        metrics = self.client.fetch_channel_metrics(str(channel_id))
        self.analytics_repo.save_snapshot(
            channel_id=channel_id,
            views=metrics.views,
            watch_time=metrics.watch_time,
            subs=metrics.subs,
            ctr=metrics.ctr,
            top_videos=metrics.top_videos,
            captured_at=datetime.utcnow(),
        )
        logger.info("analytics snapshot captured", channel_id=channel_id)
        return metrics

    def latest_snapshot(self, channel_id: int) -> dict[str, str] | None:
        snapshot = self.analytics_repo.latest_snapshot(channel_id)
        if not snapshot:
            return None
        return {
            "views": str(snapshot.views),
            "watch_time": f"{snapshot.watch_time:.2f}",
            "subs": str(snapshot.subs),
            "ctr": f"{snapshot.ctr:.2f}",
            "top_videos": ", ".join(snapshot.top_videos),
            "captured_at": snapshot.captured_at.isoformat(),
        }


__all__ = ["AnalyticsService"]
