from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class Channel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    credentials_ref: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ChannelCredential(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    access_token: str
    refresh_token: str
    token_uri: str
    scopes: str
    expires_at: datetime


class VideoPlan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    title: str
    description: str
    tags: list[str] = Field(sa_column_kwargs={"type_": JSON})
    schedule_at: datetime | None = None
    status: str = Field(default="draft")
    category_id: str | None = None
    video_path: str | None = None
    thumbnail_path: str | None = None


class UploadJob(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_plan_id: int = Field(foreign_key="videoplan.id")
    state: str = Field(default="pending")
    result_ref: str | None = None
    error_message: str | None = None
    attempts: int = Field(default=0)


class CommentRule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    pattern: str
    action: str
    template_ref: str | None = None


class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    video_id: str
    author: str
    text: str
    flagged: bool = Field(default=False)
    requires_approval: bool = Field(default=False)

class CommentReplyQueue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    comment_id: int = Field(foreign_key="comment.id")
    template_ref: str
    approved: bool = Field(default=False)


class AnalyticsSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    views: int
    watch_time: float
    subs: int
    ctr: float
    top_videos: list[str] = Field(sa_column_kwargs={"type_": JSON})


class NotificationRule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")
    metric: str
    threshold: float
    direction: str = Field(default="above")
    channel: str = Field(default="email")


class ABVariant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_plan_id: int = Field(foreign_key="videoplan.id")
    target: str
    variant_label: str
    payload: dict = Field(sa_column_kwargs={"type_": JSON})
    active: bool = Field(default=True)


class SubtitleTrack(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_plan_id: int = Field(foreign_key="videoplan.id")
    language: str
    content: str
    status: str = Field(default="draft")


class SponsorDeal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_plan_id: int = Field(foreign_key="videoplan.id")
    sponsor_name: str
    utm_parameters: dict = Field(sa_column_kwargs={"type_": JSON})
    revenue_share: float | None = None


class CrosspostTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_plan_id: int = Field(foreign_key="videoplan.id")
    platform: str
    payload: dict = Field(sa_column_kwargs={"type_": JSON})
    state: str = Field(default="pending")


__all__ = [
    "Channel",
    "ChannelCredential",
    "VideoPlan",
    "UploadJob",
    "CommentRule",
    "Comment",
    "CommentReplyQueue",
    "AnalyticsSnapshot",
    "NotificationRule",
    "ABVariant",
    "SubtitleTrack",
    "SponsorDeal",
    "CrosspostTask",
]
