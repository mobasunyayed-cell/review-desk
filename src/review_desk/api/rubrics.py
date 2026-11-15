"""Rubric endpoints."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select

from review_desk.agreement import reviewer_agreement
from review_desk.api.deps import SessionDep, current_user
from review_desk.export import export_rows, to_csv
from review_desk.models import Criterion, Rubric
from review_desk.schemas import AgreementOut, RubricCreate, RubricOut

router = APIRouter(prefix="/rubrics", tags=["rubrics"], dependencies=[Depends(current_user)])


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


@router.get("/{rubric_id}/agreement", response_model=AgreementOut)
def get_agreement(
    rubric_id: int,
    session: SessionDep,
    reviewer_a: Annotated[str, Query(min_length=1, max_length=100)],
    reviewer_b: Annotated[str, Query(min_length=1, max_length=100)],
) -> AgreementOut:
    """Cohen's kappa between two reviewers for each criterion of a rubric."""
    first, second = reviewer_a.strip().lower(), reviewer_b.strip().lower()
    if first == second:
        raise HTTPException(422, "choose two different reviewers")
    rubric = session.get(Rubric, rubric_id)
    if rubric is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rubric not found")
    return reviewer_agreement(session, rubric, first, second)


@router.get("/{rubric_id}/export", response_model=None)
def export_reviews(
    rubric_id: int,
    session: SessionDep,
    format: Literal["csv", "json"] = "json",  # noqa: A002 - public query parameter name
) -> Response | list[dict[str, Any]]:
    """Every review of this rubric as flat rows, for spreadsheets or further analysis."""
    rubric = session.get(Rubric, rubric_id)
    if rubric is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rubric not found")
    rows = export_rows(session, rubric)
    if format == "json":
        return rows
    return Response(
        to_csv(rubric, rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="rubric-{rubric_id}-reviews.csv"'},
    )
