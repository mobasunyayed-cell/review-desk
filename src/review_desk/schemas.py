"""Request and response shapes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
