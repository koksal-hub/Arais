from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.repo.credentials import CredentialsRepository
from app.repo.videos import VideoRepository
from app.services.video import VideoUploadService
from app.yt.mock_uploader import MockYouTubeUploadClient


@pytest.fixture()
def setup_repos() -> tuple[CredentialsRepository, VideoRepository]:
    cred_repo = CredentialsRepository()
    video_repo = VideoRepository()
    channel = cred_repo.create_channel("Test Kanal", "default")
    cred_repo.upsert_credentials(
        channel_id=channel.id,
        access_token="token",
        refresh_token="refresh",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["scope1"],
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return cred_repo, video_repo


@pytest.fixture()
def service(setup_repos: tuple[CredentialsRepository, VideoRepository]) -> VideoUploadService:
    cred_repo, video_repo = setup_repos
    client = MockYouTubeUploadClient()
    return VideoUploadService(video_repo=video_repo, cred_repo=cred_repo, client=client)


def test_create_plan_and_dry_run(service: VideoUploadService):
    plan_id = service.create_plan(
        channel_id=1,
        title="Deneme Video",
        description="Açıklama",
        tags=["test", "video"],
        schedule_at=datetime.utcnow() + timedelta(hours=2),
        category_id="22",
        video_path="/tmp/video.mp4",
        thumbnail_path="/tmp/thumb.jpg",
    )
    result = service.run_upload_job(plan_id, dry_run=True)
    assert result.status == "dry-run"


def test_missing_video_file(service: VideoUploadService):
    plan_id = service.create_plan(
        channel_id=1,
        title="Video",
        description="Açıklama",
        tags=["deneme"],
        schedule_at=None,
        category_id="22",
        video_path=None,
        thumbnail_path=None,
    )
    with pytest.raises(Exception):
        service.run_upload_job(plan_id)
