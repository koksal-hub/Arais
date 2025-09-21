from __future__ import annotations

from app.repo.credentials import CredentialsRepository
from app.repo.videos import VideoRepository
from app.services.archive import ArchiveService


def test_archive_exports_json_and_csv():
    cred_repo = CredentialsRepository()
    video_repo = VideoRepository()
    channel = cred_repo.create_channel("Arşiv", "default")
    video_repo.create_plan(
        channel_id=channel.id,
        title="Arşiv Video",
        description="Test",
        tags=["arsiv"],
        schedule_at=None,
        status="draft",
        category_id=None,
        video_path=None,
        thumbnail_path=None,
    )
    service = ArchiveService()
    json_output = service.export_videos(format="json")
    csv_output = service.export_videos(format="csv")
    assert "Arşiv Video" in json_output
    assert "title" in csv_output.splitlines()[0]
