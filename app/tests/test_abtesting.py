from __future__ import annotations

from app.repo.abtesting import ABTestingRepository
from app.services.abtesting import ABTestingService


def test_ab_testing_selects_winner():
    repo = ABTestingRepository()
    service = ABTestingService(repo)
    service.create_variant(1, "title", "A", {"title": "A"})
    service.create_variant(1, "title", "B", {"title": "B"})
    winner = service.decide_winner(1, {"A": 0.4, "B": 0.6})
    assert winner == "B"
