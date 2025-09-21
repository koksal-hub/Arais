from __future__ import annotations

from app.repo.subtitles import SubtitleRepository
from app.services.subtitles import SubtitleService


def test_subtitle_creation_and_approval():
    repo = SubtitleRepository()
    service = SubtitleService(repo)
    track_id = service.create_track(1, "tr", "Merhaba dünya")
    service.approve_track(track_id)
    tracks = service.list_tracks(1)
    assert tracks[0]["status"] == "approved"
