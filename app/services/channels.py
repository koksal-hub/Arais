from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.models.base import Channel
from app.repo.credentials import CredentialsRepository


@dataclass(slots=True)
class ChannelInfo:
    id: int
    title: str
    credentials_ref: str


class ChannelService:
    def __init__(self, repo: CredentialsRepository) -> None:
        self.repo = repo

    def register_channel(self, title: str, credentials_ref: str) -> ChannelInfo:
        channel = self.repo.create_channel(title, credentials_ref)
        return ChannelInfo(id=channel.id, title=channel.title, credentials_ref=channel.credentials_ref)

    def list_channels(self) -> List[ChannelInfo]:
        from app.repo.database import session_scope
        from sqlmodel import select

        with session_scope() as session:
            channels = session.exec(select(Channel)).all()
        return [ChannelInfo(id=ch.id, title=ch.title, credentials_ref=ch.credentials_ref) for ch in channels]


__all__ = ["ChannelService", "ChannelInfo"]
