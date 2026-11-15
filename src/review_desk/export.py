"""Flatten a rubric's reviews into rows for CSV or JSON export."""

from __future__ import annotations

import csv
import io
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from review_desk.models import Review, Rubric, Task

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: Any) -> Any:
    """Neutralise spreadsheet formulas ("CSV injection") in user-supplied text.

    A reviewer comment such as ``=HYPERLINK(...)`` would otherwise run when the file is
    opened in Excel or Sheets. Prefixing an apostrophe makes the cell plain text.
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def export_rows(session: Session, rubric: Rubric) -> list[dict[str, Any]]:
    """One row per review of this rubric: who, what, each criterion score, the total."""
    query = (
        select(Review, Task)
        .join(Task, Task.id == Review.task_id)
        .where(Review.rubric_id == rubric.id)
        .order_by(Review.id)
    )
    rows: list[dict[str, Any]] = []
    for review, task in session.execute(query):
        by_criterion = {s.criterion_id: s.score for s in review.scores}
        row: dict[str, Any] = {
            "review_id": review.id,
            "task_id": task.id,
            "task_title": task.title,
            "reviewer": review.reviewer,
            "created_at": review.created_at.isoformat(),
        }
        for criterion in rubric.criteria:
            row[criterion.name] = by_criterion.get(criterion.id)
        row["total"] = round(review.total, 4)
        row["comment"] = review.comment
        rows.append(row)
    return rows


def columns(rubric: Rubric) -> list[str]:
    fixed = ["review_id", "task_id", "task_title", "reviewer", "created_at"]
    return [*fixed, *(c.name for c in rubric.criteria), "total", "comment"]


def to_csv(rubric: Rubric, rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns(rubric), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: safe_cell(value) for key, value in row.items()})
    return buffer.getvalue()
