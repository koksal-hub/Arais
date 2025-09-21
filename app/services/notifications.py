from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.logging import get_logger
from app.core.retry import retry
from app.repo.notifications import NotificationRepository

logger = get_logger(__name__)


class Notifier(Protocol):
    def send(self, *, subject: str, body: str) -> None: ...


@dataclass(slots=True)
class EmailNotifier:
    sender: str
    recipient: str

    def send(self, *, subject: str, body: str) -> None:
        logger.info("email notification", sender=self.sender, recipient=self.recipient, subject=subject)


@dataclass(slots=True)
class SlackNotifier:
    webhook_url: str

    def send(self, *, subject: str, body: str) -> None:
        logger.info("slack notification", webhook=self.webhook_url, title=subject, body=body)


class NotificationService:
    def __init__(
        self,
        *,
        repo: NotificationRepository,
        email_notifier: Notifier,
        slack_notifier: Notifier,
    ) -> None:
        self.repo = repo
        self.email_notifier = email_notifier
        self.slack_notifier = slack_notifier

    def evaluate_metric(self, channel_id: int, metric: str, value: float) -> list[str]:
        triggered: list[str] = []
        for rule in self.repo.list_rules(channel_id):
            should_notify = False
            if rule.metric != metric:
                continue
            if rule.direction == "above" and value >= rule.threshold:
                should_notify = True
            if rule.direction == "below" and value <= rule.threshold:
                should_notify = True
            if should_notify:
                subject = f"{metric} eşiği aşıldı"
                body = f"Metric {metric} değeri {value} olarak ölçüldü."
                notifier = self.email_notifier if rule.channel == "email" else self.slack_notifier
                retry(lambda: notifier.send(subject=subject, body=body), retries=2, sleep_func=lambda _: None)
                triggered.append(rule.channel)
                logger.info("notification sent", metric=metric, value=value, channel=rule.channel)
        return triggered

    def notify_error(self, message: str) -> None:
        retry(lambda: self.slack_notifier.send(subject="Hata", body=message), retries=2, sleep_func=lambda _: None)


__all__ = ["NotificationService", "EmailNotifier", "SlackNotifier"]
