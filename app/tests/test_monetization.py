from __future__ import annotations

from app.repo.sponsor import SponsorRepository
from app.services.monetization import MonetizationService


def test_monetization_summary():
    repo = SponsorRepository()
    service = MonetizationService(repo)
    service.register_sponsorship(1, "Firma", {"utm_source": "youtube"}, 0.2)
    summary = service.sponsorship_summary(1)
    assert summary[0]["sponsor"] == "Firma"
