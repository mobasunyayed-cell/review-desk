"""Task endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from review_desk.api.deps import SessionDep
from review_desk.models import Task, TaskStatus
from review_desk.schemas import TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: SessionDep) -> Task:
    task = Task(**payload.model_dump())
    session.add(task)
    session.commit()
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    session: SessionDep,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Task]:
    query = select(Task).order_by(Task.id).limit(limit).offset(offset)
    if task_status is not None:
        query = query.where(Task.status == task_status)
    return list(session.scalars(query))


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, session: SessionDep) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    return task
