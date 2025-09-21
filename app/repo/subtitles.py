from __future__ import annotations

from typing import Iterable

from sqlmodel import select

from app.models.base import SubtitleTrack
from app.repo.database import session_scope


class SubtitleRepository:
    def add_track(self, video_plan_id: int, language: str, content: str, status: str = "draft") -> SubtitleTrack:
        with session_scope() as session:
            track = SubtitleTrack(video_plan_id=video_plan_id, language=language, content=content, status=status)
            session.add(track)
            session.flush()
            return track

    def update_status(self, track_id: int, status: str) -> None:
        with session_scope() as session:
            track = session.get(SubtitleTrack, track_id)
            if not track:
                return
            track.status = status
            session.add(track)

    def list_tracks(self, video_plan_id: int) -> list[SubtitleTrack]:
        with session_scope() as session:
            statement = select(SubtitleTrack).where(SubtitleTrack.video_plan_id == video_plan_id)
            return list(session.exec(statement))


__all__ = ["SubtitleRepository"]
