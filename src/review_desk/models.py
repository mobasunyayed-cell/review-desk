"""Database tables."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from review_desk.db import Base, UTCDateTime
from review_desk.scoring import weighted_total


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


class Rubric(Base):
    """A named set of weighted criteria used to score a response."""

    __tablename__ = "rubrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    criteria: Mapped[list[Criterion]] = relationship(
        back_populates="rubric",
        cascade="all, delete-orphan",
        order_by="Criterion.id",
        lazy="selectin",
    )


class Criterion(Base):
    __tablename__ = "criteria"
    __table_args__ = (UniqueConstraint("rubric_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float]
    max_score: Mapped[int]
    rubric: Mapped[Rubric] = relationship(back_populates="criteria")


class Review(Base):
    """One reviewer's scores for one task. A reviewer can review a task only once."""

    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("task_id", "reviewer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id"))
    reviewer: Mapped[str] = mapped_column(String(100))
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)
    scores: Mapped[list[ReviewScore]] = relationship(
        cascade="all, delete-orphan", order_by="ReviewScore.criterion_id", lazy="selectin"
    )

    @property
    def total(self) -> float:
        """Weighted score from 0 to 1."""
        if not self.scores:
            return 0.0
        return weighted_total(
            (s.criterion.weight, s.criterion.max_score, s.score) for s in self.scores
        )


class ReviewScore(Base):
    __tablename__ = "review_scores"

    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("criteria.id"), primary_key=True)
    score: Mapped[int]
    criterion: Mapped[Criterion] = relationship(lazy="selectin")
