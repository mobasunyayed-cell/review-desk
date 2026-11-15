import pytest

from conftest import sign_in

TASK = {"title": "Aspirin", "prompt": "Dose?", "ai_response": "It depends."}
RUBRIC = {
    "name": "Accuracy and safety",
    "criteria": [
        {"name": "Accuracy", "weight": 3, "max_score": 5},
        {"name": "Safety", "weight": 1, "max_score": 10},
    ],
}


@pytest.fixture
def setup(client):
    task = client.post("/tasks", json=TASK).json()
    rubric = client.post("/rubrics", json=RUBRIC).json()
    ids = [c["id"] for c in rubric["criteria"]]
    return client, task["id"], rubric["id"], ids


def review(rubric_id, ids, scores, **extra):
    return {
        "rubric_id": rubric_id,
        "scores": [{"criterion_id": i, "score": s} for i, s in zip(ids, scores, strict=True)],
        **extra,
    }


def test_review_computes_weighted_total_and_marks_task_reviewed(setup):
    client, task_id, rubric_id, ids = setup
    # accuracy 5/5 (weight 3) and safety 5/10 (weight 1): (3*1.0 + 1*0.5) / 4 = 0.875
    response = client.post(
        f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [5, 5], comment="Solid")
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == pytest.approx(0.875)
    assert body["comment"] == "Solid" and body["task_id"] == task_id
    assert body["reviewer"] == "dr-a"  # taken from the login, not from the request
    assert [s["score"] for s in body["scores"]] == [5, 5]
    assert client.get(f"/tasks/{task_id}").json()["status"] == "reviewed"


def test_reviewer_cannot_be_chosen_in_the_request(setup):
    client, task_id, rubric_id, ids = setup
    body = review(rubric_id, ids, [1, 1], reviewer="someone-else")
    response = client.post(f"/tasks/{task_id}/reviews", json=body)
    assert response.json()["reviewer"] == "dr-a"


def test_list_reviews_for_a_task(setup):
    client, task_id, rubric_id, ids = setup
    other = sign_in(client, "dr-b")
    client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [5, 10]))
    client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [0, 0]), headers=other)
    listed = client.get(f"/tasks/{task_id}/reviews").json()
    assert [r["reviewer"] for r in listed] == ["dr-a", "dr-b"]
    assert [r["total"] for r in listed] == [1.0, 0.0]


def test_same_reviewer_cannot_review_twice_but_can_review_another_task(setup):
    client, task_id, rubric_id, ids = setup
    other = client.post("/tasks", json=TASK).json()["id"]
    first = client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [1, 1]))
    assert first.status_code == 201
    again = client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [2, 2]))
    assert again.status_code == 409
    elsewhere = client.post(f"/tasks/{other}/reviews", json=review(rubric_id, ids, [2, 2]))
    assert elsewhere.status_code == 201


def test_unknown_task_or_rubric_is_404(setup):
    client, task_id, rubric_id, ids = setup
    assert client.post("/tasks/999/reviews", json=review(rubric_id, ids, [1, 1])).status_code == 404
    assert client.get("/tasks/999/reviews").status_code == 404
    assert (
        client.post(f"/tasks/{task_id}/reviews", json=review(999, ids, [1, 1])).status_code == 404
    )


def test_every_criterion_must_be_scored_exactly_once(setup):
    client, task_id, rubric_id, ids = setup
    url = f"/tasks/{task_id}/reviews"
    missing = {"rubric_id": rubric_id, "scores": [{"criterion_id": ids[0], "score": 1}]}
    assert "missing" in client.post(url, json=missing).json()["detail"]
    twice = review(rubric_id, [ids[0], ids[0]], [1, 1])
    assert "only once" in client.post(url, json=twice).json()["detail"]
    foreign = review(rubric_id, [ids[0], 12345], [1, 1])
    assert "not in this rubric" in client.post(url, json=foreign).json()["detail"]


@pytest.mark.parametrize("scores", [[6, 5], [5, 11]])
def test_score_above_maximum_is_rejected(setup, scores):
    client, task_id, rubric_id, ids = setup
    response = client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, scores))
    assert response.status_code == 422 and "exceeds" in response.json()["detail"]
    assert client.get(f"/tasks/{task_id}").json()["status"] == "pending"  # nothing was saved


def test_negative_score_is_rejected(setup):
    client, task_id, rubric_id, ids = setup
    response = client.post(f"/tasks/{task_id}/reviews", json=review(rubric_id, ids, [-1, 1]))
    assert response.status_code == 422
