from __future__ import annotations

import pytest

from app.repo.credentials import CredentialsRepository
from app.services.auth import AuthService
from app.yt.mock_client import MockYouTubeAuthClient


@pytest.fixture()
def repo() -> CredentialsRepository:
    repository = CredentialsRepository()
    repository.create_channel("Test Kanal", "default")
    return repository


@pytest.fixture()
def service(repo: CredentialsRepository) -> AuthService:
    client = MockYouTubeAuthClient()
    return AuthService(repo=repo, client=client)


def test_device_flow_success(service: AuthService, repo: CredentialsRepository):
    channel = repo.get_channel(1)
    client = service.client  # type: ignore[attr-defined]
    device = service.begin_device_flow(channel.id, scopes=["scope1"])
    assert device.verification_uri == "https://youtube.com/device"
    client.authorize_device(device.device_code, scopes=["scope1"])
    payload = service.complete_device_flow(channel.id, device.device_code, scopes=["scope1"])
    assert payload.access_token.startswith("ya29.")


def test_refresh_credentials(service: AuthService, repo: CredentialsRepository):
    channel = repo.get_channel(1)
    client = service.client  # type: ignore[attr-defined]
    device = service.begin_device_flow(channel.id, scopes=["scope1"])
    client.authorize_device(device.device_code, scopes=["scope1"])
    payload = service.complete_device_flow(channel.id, device.device_code, scopes=["scope1"])
    refreshed = service.refresh_channel_credentials(channel.id, scopes=["scope1"])
    assert refreshed.refresh_token == payload.refresh_token


def test_device_flow_pending(service: AuthService, repo: CredentialsRepository):
    channel = repo.get_channel(1)
    device = service.begin_device_flow(channel.id, scopes=["scope1"])
    with pytest.raises(Exception):
        service.complete_device_flow(channel.id, device.device_code, scopes=["scope1"])
