"""Database tables."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from review_desk.db import Base, UTCDateTime


class TaskStatus(str, enum.Enum):
    pending = "pending"
    reviewed = "reviewed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Task(Base):
    """One AI response waiting for review."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.pending, index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)
