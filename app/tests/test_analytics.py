from __future__ import annotations

from app.repo.analytics import AnalyticsRepository
from app.repo.credentials import CredentialsRepository
from app.services.analytics import AnalyticsService
from app.yt.mock_analytics import MockYouTubeAnalyticsClient


def test_collect_and_fetch_snapshot():
    analytics_repo = AnalyticsRepository()
    cred_repo = CredentialsRepository()
    client = MockYouTubeAnalyticsClient()
    channel = cred_repo.create_channel("Analytics Kanal", "default")
    service = AnalyticsService(analytics_repo=analytics_repo, credentials_repo=cred_repo, client=client)

    metrics = service.collect_snapshot(channel.id)
    assert metrics.views > 0
    snapshot = service.latest_snapshot(channel.id)
    assert snapshot is not None
    assert "views" in snapshot
