from __future__ import annotations

from typing import Iterable

from app.repo.sponsor import SponsorRepository


class MonetizationService:
    def __init__(self, repo: SponsorRepository) -> None:
        self.repo = repo

    def register_sponsorship(self, video_plan_id: int, sponsor_name: str, utm_parameters: dict, revenue_share: float | None = None) -> int:
        deal = self.repo.create_deal(video_plan_id, sponsor_name, utm_parameters, revenue_share)
        return deal.id

    def sponsorship_summary(self, video_plan_id: int) -> list[dict[str, str]]:
        deals = self.repo.list_deals(video_plan_id)
        summary: list[dict[str, str]] = []
        for deal in deals:
            summary.append(
                {
                    "sponsor": deal.sponsor_name,
                    "utm": ",".join(f"{k}={v}" for k, v in deal.utm_parameters.items()),
                    "revenue_share": str(deal.revenue_share or 0.0),
                }
            )
        return summary


__all__ = ["MonetizationService"]
