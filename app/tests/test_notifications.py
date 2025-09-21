from __future__ import annotations

from dataclasses import dataclass

from app.repo.notifications import NotificationRepository
from app.services.notifications import EmailNotifier, NotificationService, SlackNotifier


@dataclass
class CaptureNotifier:
    sent: list[tuple[str, str]]

    def send(self, *, subject: str, body: str) -> None:
        self.sent.append((subject, body))


def test_notifications_trigger_threshold():
    repo = NotificationRepository()
    email_capture = CaptureNotifier(sent=[])
    slack_capture = CaptureNotifier(sent=[])
    service = NotificationService(
        repo=repo,
        email_notifier=email_capture,
        slack_notifier=slack_capture,
    )
    repo.create_rule(channel_id=1, metric="views", threshold=1000, direction="above", channel="email")
    repo.create_rule(channel_id=1, metric="views", threshold=5000, direction="above", channel="slack")

    triggered = service.evaluate_metric(1, "views", 6000)
    assert set(triggered) == {"email", "slack"}
    assert len(email_capture.sent) == 1
    assert len(slack_capture.sent) == 1
