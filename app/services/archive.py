from __future__ import annotations

import csv
import io
import json
from typing import Literal

from sqlmodel import select

from app.models.base import VideoPlan
from app.repo.database import session_scope


class ArchiveService:
    def export_videos(self, *, format: Literal["json", "csv"] = "json") -> str:
        with session_scope() as session:
            plans = session.exec(select(VideoPlan)).all()
        data = [
            {
                "id": plan.id,
                "title": plan.title,
                "description": plan.description,
                "tags": ",".join(plan.tags),
                "status": plan.status,
            }
            for plan in plans
        ]
        if format == "json":
            return json.dumps(data, ensure_ascii=False)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["id", "title", "description", "tags", "status"])
        writer.writeheader()
        for item in data:
            writer.writerow(item)
        return buffer.getvalue()


__all__ = ["ArchiveService"]
