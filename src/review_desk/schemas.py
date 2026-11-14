"""Request and response shapes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from review_desk.models import TaskStatus


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    ai_response: str = Field(min_length=1)


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    prompt: str
    ai_response: str
    status: TaskStatus
    created_at: datetime


class CriterionIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    weight: float = Field(default=1.0, gt=0, le=100)
    max_score: int = Field(default=5, ge=1, le=10)


class CriterionOut(CriterionIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RubricCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    criteria: list[CriterionIn] = Field(min_length=1, max_length=30)

    @field_validator("criteria")
    @classmethod
    def names_must_be_unique(cls, value: list[CriterionIn]) -> list[CriterionIn]:
        names = [c.name.lower() for c in value]
        if len(names) != len(set(names)):
            raise ValueError("criterion names must be unique within a rubric")
        return value


class RubricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    criteria: list[CriterionOut]


class ScoreIn(BaseModel):
    criterion_id: int
    score: int = Field(ge=0)


class ReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rubric_id: int
    reviewer: str = Field(min_length=1, max_length=100)
    scores: list[ScoreIn] = Field(min_length=1)
    comment: str = Field(default="", max_length=2000)


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criterion_id: int
    score: int


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    rubric_id: int
    reviewer: str
    comment: str
    created_at: datetime
    total: float
    scores: list[ScoreOut]
