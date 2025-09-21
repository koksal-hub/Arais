from __future__ import annotations

from typing import Iterable

from sqlmodel import select

from app.models.base import ABVariant
from app.repo.database import session_scope


class ABTestingRepository:
    def create_variant(self, video_plan_id: int, target: str, label: str, payload: dict) -> ABVariant:
        with session_scope() as session:
            variant = ABVariant(video_plan_id=video_plan_id, target=target, variant_label=label, payload=payload)
            session.add(variant)
            session.flush()
            return variant

    def list_variants(self, video_plan_id: int) -> list[ABVariant]:
        with session_scope() as session:
            statement = select(ABVariant).where(ABVariant.video_plan_id == video_plan_id, ABVariant.active.is_(True))
            return list(session.exec(statement))

    def deactivate_variant(self, variant_id: int) -> None:
        with session_scope() as session:
            variant = session.get(ABVariant, variant_id)
            if variant:
                variant.active = False
                session.add(variant)


__all__ = ["ABTestingRepository"]
