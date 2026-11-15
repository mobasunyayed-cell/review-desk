"""How much do two reviewers agree? Uses Cohen's kappa from medeval."""

from __future__ import annotations

import math

from medeval.agreement import cohens_kappa, interpret_kappa
from sqlalchemy import select
from sqlalchemy.orm import Session

from review_desk.models import Review, Rubric
from review_desk.schemas import AgreementOut, CriterionAgreement


def reviewer_agreement(
    session: Session, rubric: Rubric, reviewer_a: str, reviewer_b: str
) -> AgreementOut:
    """Quadratic-weighted kappa per criterion over the tasks both reviewers scored.

    Scores are ordered (0 to the criterion's maximum), so a one-point disagreement counts for
    much less than a four-point one. With too few shared tasks, or when a reviewer always gives
    the same score, kappa is undefined and is reported as null.
    """
    reviews = session.scalars(
        select(Review).where(
            Review.rubric_id == rubric.id, Review.reviewer.in_([reviewer_a, reviewer_b])
        )
    )
    by_task: dict[int, dict[str, Review]] = {}
    for review in reviews:
        by_task.setdefault(review.task_id, {})[review.reviewer] = review
    shared = [pair for _, pair in sorted(by_task.items()) if len(pair) == 2]

    results: list[CriterionAgreement] = []
    for criterion in rubric.criteria:
        a_scores: list[str] = []
        b_scores: list[str] = []
        for pair in shared:
            a_scores.append(str(_score(pair[reviewer_a], criterion.id)))
            b_scores.append(str(_score(pair[reviewer_b], criterion.id)))
        if shared:
            categories = [str(i) for i in range(criterion.max_score + 1)]
            kappa = cohens_kappa(a_scores, b_scores, categories, weights="quadratic")
            exact = sum(x == y for x, y in zip(a_scores, b_scores, strict=True)) / len(shared)
        else:
            kappa, exact = math.nan, None
        results.append(
            CriterionAgreement(
                criterion_id=criterion.id,
                name=criterion.name,
                kappa=None if math.isnan(kappa) else round(kappa, 4),
                interpretation=interpret_kappa(kappa),
                exact_agreement=exact,
            )
        )

    defined = [r.kappa for r in results if r.kappa is not None]
    return AgreementOut(
        rubric_id=rubric.id,
        reviewer_a=reviewer_a,
        reviewer_b=reviewer_b,
        shared_tasks=len(shared),
        mean_kappa=round(sum(defined) / len(defined), 4) if defined else None,
        criteria=results,
    )


def _score(review: Review, criterion_id: int) -> int:
    return next(s.score for s in review.scores if s.criterion_id == criterion_id)
