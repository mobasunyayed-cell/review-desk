import pytest

from review_desk.scoring import weighted_total


def test_perfect_and_zero():
    assert weighted_total([(1.0, 5, 5), (2.0, 10, 10)]) == pytest.approx(1.0)
    assert weighted_total([(1.0, 5, 0), (2.0, 10, 0)]) == 0.0


def test_scores_are_scaled_to_their_own_maximum():
    # 5/5 and 5/10 with equal weight -> (1.0 + 0.5) / 2
    assert weighted_total([(1.0, 5, 5), (1.0, 10, 5)]) == pytest.approx(0.75)


def test_weights_matter():
    # a heavy criterion at 0% drags the total down more than a light one
    heavy = weighted_total([(3.0, 5, 0), (1.0, 5, 5)])
    light = weighted_total([(1.0, 5, 0), (3.0, 5, 5)])
    assert heavy == pytest.approx(0.25) and light == pytest.approx(0.75)


@pytest.mark.parametrize(
    "items",
    [[], [(0.0, 5, 1)], [(-1.0, 5, 1)], [(1.0, 0, 0)], [(1.0, 5, 6)], [(1.0, 5, -1)]],
)
def test_invalid_input_is_rejected(items):
    with pytest.raises(ValueError):
        weighted_total(items)
