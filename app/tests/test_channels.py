from __future__ import annotations

from app.repo.credentials import CredentialsRepository
from app.services.channels import ChannelService


def test_channel_registration_and_listing():
    repo = CredentialsRepository()
    service = ChannelService(repo)
    service.register_channel("Ana Kanal", "default")
    service.register_channel("Oyun", "profile2")
    channels = service.list_channels()
    assert len(channels) == 2
    assert channels[0].title == "Ana Kanal"
