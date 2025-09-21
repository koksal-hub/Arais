from __future__ import annotations

from typing import Dict

from app.repo.abtesting import ABTestingRepository


class ABTestingService:
    def __init__(self, repo: ABTestingRepository) -> None:
        self.repo = repo

    def create_variant(self, video_plan_id: int, target: str, label: str, payload: dict) -> int:
        variant = self.repo.create_variant(video_plan_id, target, label, payload)
        return variant.id

    def decide_winner(self, video_plan_id: int, performance: Dict[str, float]) -> str | None:
        variants = self.repo.list_variants(video_plan_id)
        best_label = None
        best_score = float("-inf")
        for variant in variants:
            score = performance.get(variant.variant_label)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_label = variant.variant_label
        if best_label is not None:
            for variant in variants:
                if variant.variant_label != best_label:
                    self.repo.deactivate_variant(variant.id)
        return best_label


__all__ = ["ABTestingService"]
