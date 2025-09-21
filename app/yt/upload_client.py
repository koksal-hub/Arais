from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class UploadResult:
    video_id: str
    publish_at: datetime | None
    status: str


class YouTubeUploadClient(Protocol):
    def upload(
        self,
        *,
        title: str,
        description: str,
        tags: list[str],
        category_id: str | None,
        video_path: str,
        thumbnail_path: str | None,
        publish_at: datetime | None,
        privacy_status: str,
        dry_run: bool = False,
    ) -> UploadResult: ...


__all__ = ["YouTubeUploadClient", "UploadResult"]
