from __future__ import annotations

from datetime import datetime
from typing import Sequence

from app.core.errors import AppException, NotFoundError, RateLimitError
from app.core.logging import get_logger
from app.core.retry import retry
from app.repo.credentials import CredentialsRepository
from app.yt.client import YouTubeAuthClient
from app.yt.types import DeviceCode, TokenPayload

logger = get_logger(__name__)


class AuthService:
    def __init__(self, repo: CredentialsRepository, client: YouTubeAuthClient) -> None:
        self.repo = repo
        self.client = client

    def begin_device_flow(self, channel_id: int, scopes: Sequence[str]) -> DeviceCode:
        channel = self.repo.get_channel(channel_id)
        if not channel:
            raise NotFoundError("Kanal bulunamadı")
        return self.client.start_device_authorization(scopes)

    def complete_device_flow(self, channel_id: int, device_code: str, scopes: Sequence[str]) -> TokenPayload:
        channel = self.repo.get_channel(channel_id)
        if not channel:
            raise NotFoundError("Kanal bulunamadı")

        def operation() -> TokenPayload:
            return self.client.poll_device_authorization(device_code)

        try:
            payload = retry(operation, retries=5, exceptions=(PermissionError, RateLimitError), sleep_func=lambda _: None)
        except PermissionError as exc:  # pragma: no cover - yet to authorize
            raise AppException("Yetkilendirme henüz tamamlanmadı") from exc

        self.repo.upsert_credentials(
            channel_id=channel_id,
            access_token=payload.access_token,
            refresh_token=payload.refresh_token,
            token_uri=payload.token_uri,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )
        logger.info("credentials stored", channel_id=channel_id)
        return payload

    def refresh_channel_credentials(self, channel_id: int, scopes: Sequence[str]) -> TokenPayload:
        credentials = self.repo.get_credentials(channel_id)
        if not credentials:
            raise NotFoundError("Kanal kimlik bilgisi bulunamadı")

        payload = self.client.refresh_access_token(credentials.refresh_token, scopes)
        self.repo.upsert_credentials(
            channel_id=channel_id,
            access_token=payload.access_token,
            refresh_token=payload.refresh_token,
            token_uri=payload.token_uri,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )
        return payload


__all__ = ["AuthService"]
