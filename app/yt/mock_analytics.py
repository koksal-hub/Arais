from __future__ import annotations

import random
from datetime import datetime

from app.yt.analytics_client import AnalyticsResult, YouTubeAnalyticsClient


class MockYouTubeAnalyticsClient(YouTubeAnalyticsClient):
    def fetch_channel_metrics(self, channel_id: str, *, since: datetime | None = None) -> AnalyticsResult:
        random.seed(channel_id)
        views = random.randint(1000, 100000)
        watch_time = random.uniform(500.0, 10000.0)
        subs = random.randint(10, 1000)
        ctr = round(random.uniform(1.0, 10.0), 2)
        top_videos = [f"video-{i}" for i in range(1, 4)]
        return AnalyticsResult(views=views, watch_time=watch_time, subs=subs, ctr=ctr, top_videos=top_videos)


__all__ = ["MockYouTubeAnalyticsClient"]
