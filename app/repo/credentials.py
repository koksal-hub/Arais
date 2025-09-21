from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlmodel import select

from app.models.base import Channel, ChannelCredential
from app.repo.database import session_scope


class CredentialsRepository:
    def create_channel(self, title: str, credentials_ref: str) -> Channel:
        with session_scope() as session:
            channel = Channel(title=title, credentials_ref=credentials_ref)
            session.add(channel)
            session.flush()
            return channel

    def get_channel(self, channel_id: int) -> Channel | None:
        with session_scope() as session:
            return session.get(Channel, channel_id)

    def upsert_credentials(
        self,
        *,
        channel_id: int,
        access_token: str,
        refresh_token: str,
        token_uri: str,
        scopes: Sequence[str],
        expires_at: datetime,
    ) -> ChannelCredential:
        with session_scope() as session:
            statement = select(ChannelCredential).where(ChannelCredential.channel_id == channel_id)
            existing = session.exec(statement).one_or_none()
            data = {
                "channel_id": channel_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_uri": token_uri,
                "scopes": " ".join(scopes),
                "expires_at": expires_at,
            }
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                session.add(existing)
                credential = existing
            else:
                credential = ChannelCredential(**data)
                session.add(credential)
            session.flush()
            return credential

    def get_credentials(self, channel_id: int) -> ChannelCredential | None:
        with session_scope() as session:
            statement = select(ChannelCredential).where(ChannelCredential.channel_id == channel_id)
            return session.exec(statement).one_or_none()


__all__ = ["CredentialsRepository"]
