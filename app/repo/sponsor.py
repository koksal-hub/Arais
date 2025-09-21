from __future__ import annotations

from typing import Iterable

from sqlmodel import select

from app.models.base import SponsorDeal
from app.repo.database import session_scope


class SponsorRepository:
    def create_deal(self, video_plan_id: int, sponsor_name: str, utm_parameters: dict, revenue_share: float | None = None) -> SponsorDeal:
        with session_scope() as session:
            deal = SponsorDeal(video_plan_id=video_plan_id, sponsor_name=sponsor_name, utm_parameters=utm_parameters, revenue_share=revenue_share)
            session.add(deal)
            session.flush()
            return deal

    def list_deals(self, video_plan_id: int) -> list[SponsorDeal]:
        with session_scope() as session:
            statement = select(SponsorDeal).where(SponsorDeal.video_plan_id == video_plan_id)
            return list(session.exec(statement))


__all__ = ["SponsorRepository"]
