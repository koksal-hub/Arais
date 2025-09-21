from __future__ import annotations

from app.services.content_assistant import ContentAssistantService


def test_content_suggestion_generates_keywords():
    service = ContentAssistantService()
    suggestion = service.suggest_metadata(["python", "Python", "trend"])
    assert "trend-analizi" in suggestion.tags
    assert suggestion.title.startswith("Python")
    trends = service.trend_keywords(["otomasyon"])
    assert trends == ["otomasyon-2024"]
