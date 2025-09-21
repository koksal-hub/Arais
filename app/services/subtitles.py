from __future__ import annotations

from app.repo.subtitles import SubtitleRepository


class SubtitleService:
    def __init__(self, repo: SubtitleRepository) -> None:
        self.repo = repo

    def create_track(self, video_plan_id: int, language: str, content: str) -> int:
        track = self.repo.add_track(video_plan_id, language, content, status="draft")
        return track.id

    def approve_track(self, track_id: int) -> None:
        self.repo.update_status(track_id, "approved")

    def list_tracks(self, video_plan_id: int) -> list[dict[str, str]]:
        tracks = self.repo.list_tracks(video_plan_id)
        return [{"language": track.language, "status": track.status} for track in tracks]


__all__ = ["SubtitleService"]
