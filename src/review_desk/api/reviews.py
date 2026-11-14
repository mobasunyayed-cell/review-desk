"""Review endpoints. A review scores one task against one rubric."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from review_desk.api.deps import SessionDep
from review_desk.models import Review, ReviewScore, Rubric, Task, TaskStatus
from review_desk.schemas import ReviewCreate, ReviewOut

router = APIRouter(prefix="/tasks/{task_id}/reviews", tags=["reviews"])


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(422, detail)  # literal: the constant was renamed across versions


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(task_id: int, payload: ReviewCreate, session: SessionDep) -> Review:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    rubric = session.get(Rubric, payload.rubric_id)
    if rubric is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rubric not found")

    by_id = {c.id: c for c in rubric.criteria}
    given = [s.criterion_id for s in payload.scores]
    if len(given) != len(set(given)):
        raise _unprocessable("each criterion may be scored only once")
    unknown = sorted(set(given) - set(by_id))
    if unknown:
        raise _unprocessable(f"criteria not in this rubric: {unknown}")
    missing = sorted(set(by_id) - set(given))
    if missing:
        raise _unprocessable(f"missing scores for criteria: {missing}")
    for item in payload.scores:
        limit = by_id[item.criterion_id].max_score
        if item.score > limit:
            raise _unprocessable(f"score {item.score} exceeds the maximum {limit}")

    duplicate = session.scalar(
        select(Review.id).where(Review.task_id == task_id, Review.reviewer == payload.reviewer)
    )
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "this reviewer already reviewed the task")

    review = Review(
        task_id=task_id,
        rubric_id=rubric.id,
        reviewer=payload.reviewer,
        comment=payload.comment,
        scores=[ReviewScore(criterion_id=s.criterion_id, score=s.score) for s in payload.scores],
    )
    session.add(review)
    task.status = TaskStatus.reviewed
    session.commit()
    return review


@router.get("", response_model=list[ReviewOut])
def list_reviews(task_id: int, session: SessionDep) -> list[Review]:
    if session.get(Task, task_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    query = select(Review).where(Review.task_id == task_id).order_by(Review.id)
    return list(session.scalars(query))
