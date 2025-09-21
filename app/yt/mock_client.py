from __future__ import annotations

import secrets
from typing import Sequence

from app.core.logging import get_logger
from app.yt.client import QuotaAwareMixin, YouTubeAuthClient
from app.yt.types import DeviceCode, TokenPayload

logger = get_logger(__name__)


class MockYouTubeAuthClient(QuotaAwareMixin, YouTubeAuthClient):
    """Testler için basit YouTube OAuth cihaz akışı simülasyonu."""

    def __init__(self) -> None:
        super().__init__()
        self._pending: dict[str, tuple[DeviceCode, TokenPayload | None]] = {}

    def start_device_authorization(self, scopes: Sequence[str]) -> DeviceCode:
        self._increment_quota()
        device_code = secrets.token_hex(8)
        user_code = secrets.token_hex(4).upper()
        payload = DeviceCode(
            device_code=device_code,
            user_code=user_code,
            verification_uri="https://youtube.com/device",
            expires_in=1800,
            interval=5,
        )
        self._pending[device_code] = (payload, None)
        logger.info("device code issued", device_code=device_code, scopes=list(scopes))
        return payload

    def authorize_device(self, device_code: str, *, scopes: Sequence[str]) -> None:
        if device_code not in self._pending:
            raise ValueError("unknown device code")
        token = TokenPayload.from_now(
            access_token=f"ya29.{secrets.token_hex(16)}",
            refresh_token=f"1//{secrets.token_hex(16)}",
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
            expires_in=3600,
        )
        payload, _ = self._pending[device_code]
        self._pending[device_code] = (payload, token)

    def poll_device_authorization(self, device_code: str) -> TokenPayload:
        self._increment_quota()
        if device_code not in self._pending:
            raise ValueError("unknown device code")
        payload, token = self._pending[device_code]
        if token is None:
            raise PermissionError("authorization_pending")
        return token

    def refresh_access_token(self, refresh_token: str, scopes: Sequence[str]) -> TokenPayload:
        self._increment_quota()
        return TokenPayload.from_now(
            access_token=f"ya29.{secrets.token_hex(16)}",
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
            expires_in=3600,
        )


__all__ = ["MockYouTubeAuthClient"]
