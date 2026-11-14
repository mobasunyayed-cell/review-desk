"""Rubric endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from review_desk.api.deps import SessionDep
from review_desk.models import Criterion, Rubric
from review_desk.schemas import RubricCreate, RubricOut

router = APIRouter(prefix="/rubrics", tags=["rubrics"])


@router.post("", response_model=RubricOut, status_code=status.HTTP_201_CREATED)
def create_rubric(payload: RubricCreate, session: SessionDep) -> Rubric:
    if session.scalar(select(Rubric.id).where(Rubric.name == payload.name)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "a rubric with this name already exists")
    rubric = Rubric(
        name=payload.name,
        description=payload.description,
        criteria=[Criterion(**c.model_dump()) for c in payload.criteria],
    )
    session.add(rubric)
    session.commit()
    return rubric


@router.get("", response_model=list[RubricOut])
def list_rubrics(session: SessionDep) -> list[Rubric]:
    return list(session.scalars(select(Rubric).order_by(Rubric.id)))


@router.get("/{rubric_id}", response_model=RubricOut)
def get_rubric(rubric_id: int, session: SessionDep) -> Rubric:
    rubric = session.get(Rubric, rubric_id)
    if rubric is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rubric not found")
    return rubric
