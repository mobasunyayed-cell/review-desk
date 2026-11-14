"""Score arithmetic, kept free of database code so it is easy to test."""

from __future__ import annotations

from collections.abc import Iterable


def weighted_total(items: Iterable[tuple[float, int, int]]) -> float:
    """Combine (weight, max_score, score) triples into one number from 0 to 1.

    Each score is first scaled to its own maximum, then averaged using the weights, so a
    criterion scored out of 10 and one scored out of 5 count fairly against each other.
    """
    weight_sum = 0.0
    earned = 0.0
    for weight, max_score, score in items:
        if weight <= 0:
            raise ValueError("weights must be positive")
        if max_score < 1:
            raise ValueError("max_score must be at least 1")
        if not 0 <= score <= max_score:
            raise ValueError(f"score {score} is outside 0..{max_score}")
        weight_sum += weight
        earned += weight * score / max_score
    if weight_sum == 0:
        raise ValueError("need at least one criterion")
    return earned / weight_sum
