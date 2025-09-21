from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class ContentSuggestion:
    title: str
    description: str
    tags: list[str]


class ContentAssistantService:
    def suggest_metadata(self, keywords: Sequence[str]) -> ContentSuggestion:
        normalized = [kw.lower().strip() for kw in keywords if kw]
        counter = Counter(normalized)
        top = counter.most_common(3)
        primary = top[0][0] if top else "video"
        title = f"{primary.title()} Rehberi"
        description = f"Bu videoda {primary} konusunu derinlemesine inceliyoruz."
        tags = [word for word, _ in top]
        if "trend" in normalized:
            tags.append("trend-analizi")
        return ContentSuggestion(title=title, description=description, tags=tags)

    def trend_keywords(self, base_keywords: Sequence[str]) -> list[str]:
        return [f"{kw}-2024" for kw in base_keywords]


__all__ = ["ContentAssistantService", "ContentSuggestion"]
