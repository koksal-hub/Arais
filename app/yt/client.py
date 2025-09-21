from __future__ import annotations

from typing import Protocol, Sequence

from app.core.errors import RateLimitError
from app.yt.types import DeviceCode, TokenPayload


class YouTubeAuthClient(Protocol):
    def start_device_authorization(self, scopes: Sequence[str]) -> DeviceCode: ...

    def poll_device_authorization(self, device_code: str) -> TokenPayload: ...

    def refresh_access_token(self, refresh_token: str, scopes: Sequence[str]) -> TokenPayload: ...


class QuotaAwareMixin:
    """Basit kota takibi ve 429 simülasyonu."""

    max_calls_per_minute: int = 100

    def __init__(self) -> None:
        self._call_count: int = 0

    def _increment_quota(self) -> None:
        self._call_count += 1
        if self._call_count > self.max_calls_per_minute:
            raise RateLimitError()


__all__ = ["YouTubeAuthClient", "QuotaAwareMixin"]
