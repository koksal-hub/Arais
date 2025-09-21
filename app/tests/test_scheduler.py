from __future__ import annotations

from datetime import datetime, timedelta

from app.jobs.scheduler import PlanScheduler
from app.repo.credentials import CredentialsRepository
from app.repo.videos import VideoRepository
from app.services.video import VideoUploadService
from app.yt.mock_uploader import MockYouTubeUploadClient


def test_scheduler_processes_due_plan():
    cred_repo = CredentialsRepository()
    video_repo = VideoRepository()
    client = MockYouTubeUploadClient()
    service = VideoUploadService(video_repo=video_repo, cred_repo=cred_repo, client=client)

    channel = cred_repo.create_channel("Kanal", "default")
    cred_repo.upsert_credentials(
        channel_id=channel.id,
        access_token="token",
        refresh_token="refresh",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["scope1"],
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    plan_id = service.create_plan(
        channel_id=channel.id,
        title="Planlı Video",
        description="Açıklama",
        tags=["plan"],
        schedule_at=datetime.utcnow() - timedelta(minutes=1),
        category_id="22",
        video_path="/tmp/video.mp4",
        thumbnail_path=None,
    )

    scheduler = PlanScheduler(video_repo=video_repo, video_service=service)
    processed = scheduler.process_due_plans()
    assert plan_id in processed
