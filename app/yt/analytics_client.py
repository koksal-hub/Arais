from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence


@dataclass(slots=True)
class AnalyticsResult:
    views: int
    watch_time: float
    subs: int
    ctr: float
    top_videos: list[str]


class YouTubeAnalyticsClient(Protocol):
    def fetch_channel_metrics(self, channel_id: str, *, since: datetime | None = None) -> AnalyticsResult: ...


__all__ = ["YouTubeAnalyticsClient", "AnalyticsResult"]
