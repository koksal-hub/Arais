from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence


@dataclass(slots=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int = 5


@dataclass(slots=True)
class TokenPayload:
    access_token: str
    refresh_token: str
    token_uri: str
    scopes: Sequence[str]
    expires_at: datetime

    @classmethod
    def from_now(
        cls,
        access_token: str,
        refresh_token: str,
        token_uri: str,
        scopes: Sequence[str],
        *,
        expires_in: int,
    ) -> "TokenPayload":
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            scopes=tuple(scopes),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        )


__all__ = ["DeviceCode", "TokenPayload"]
