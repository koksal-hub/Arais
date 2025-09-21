from __future__ import annotations

import secrets
from datetime import datetime

from app.yt.upload_client import UploadResult, YouTubeUploadClient


class MockYouTubeUploadClient(YouTubeUploadClient):
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
    ) -> UploadResult:
        if not title:
            raise ValueError("Başlık zorunlu")
        if not video_path:
            raise ValueError("Video dosyası belirtilmelidir")
        video_id = f"mock-{secrets.token_hex(6)}"
        status = "dry-run" if dry_run else "uploaded"
        return UploadResult(video_id=video_id, publish_at=publish_at, status=status)


__all__ = ["MockYouTubeUploadClient"]
