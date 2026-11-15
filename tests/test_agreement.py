import pytest

from conftest import sign_in

RUBRIC = {
    "name": "Quality",
    "criteria": [
        {"name": "Accuracy", "weight": 3, "max_score": 4},
        {"name": "Tone", "weight": 1, "max_score": 4},
    ],
}


@pytest.fixture
def desk(client):
    rubric = client.post("/rubrics", json=RUBRIC).json()
    ids = [c["id"] for c in rubric["criteria"]]
    other = sign_in(client, "dr-b")
    tasks = [
        client.post("/tasks", json={"title": f"t{i}", "prompt": "p", "ai_response": "r"}).json()[
            "id"
        ]
        for i in range(6)
    ]

    def rate(task_id, scores, headers=None):
        body = {
            "rubric_id": rubric["id"],
            "scores": [{"criterion_id": i, "score": s} for i, s in zip(ids, scores, strict=True)],
        }
        response = client.post(f"/tasks/{task_id}/reviews", json=body, headers=headers)
        assert response.status_code == 201
        return response

    return client, rubric["id"], ids, tasks, other, rate


def agreement(client, rubric_id, a="dr-a", b="dr-b"):
    return client.get(f"/rubrics/{rubric_id}/agreement", params={"reviewer_a": a, "reviewer_b": b})


def test_identical_reviewers_agree_perfectly(desk):
    client, rubric_id, ids, tasks, other, rate = desk
    for task, score in zip(tasks, [0, 1, 2, 3, 4, 2], strict=True):
        rate(task, [score, score])
        rate(task, [score, score], other)
    body = agreement(client, rubric_id).json()
    assert body["shared_tasks"] == 6
    assert [c["kappa"] for c in body["criteria"]] == [1.0, 1.0]
    assert body["mean_kappa"] == 1.0
    assert all(c["interpretation"] == "almost perfect" for c in body["criteria"])
    assert all(c["exact_agreement"] == 1.0 for c in body["criteria"])


def test_partial_agreement_is_between_zero_and_one(desk):
    client, rubric_id, _, tasks, other, rate = desk
    first = [0, 1, 2, 3, 4, 2]
    second = [0, 1, 3, 3, 3, 2]  # off by one on two tasks
    for task, a, b in zip(tasks, first, second, strict=True):
        rate(task, [a, a])
        rate(task, [b, b], other)
    accuracy = agreement(client, rubric_id).json()["criteria"][0]
    assert 0.5 < accuracy["kappa"] < 1.0
    assert accuracy["exact_agreement"] == pytest.approx(4 / 6)


def test_only_tasks_reviewed_by_both_count(desk):
    client, rubric_id, _, tasks, other, rate = desk
    rate(tasks[0], [1, 1])
    rate(tasks[0], [1, 1], other)
    rate(tasks[1], [4, 4])  # only dr-a reviewed this one
    body = agreement(client, rubric_id).json()
    assert body["shared_tasks"] == 1


def test_no_shared_tasks_gives_null_kappa(desk):
    client, rubric_id, _, tasks, other, rate = desk
    rate(tasks[0], [1, 1])
    rate(tasks[1], [1, 1], other)
    body = agreement(client, rubric_id).json()
    assert body["shared_tasks"] == 0 and body["mean_kappa"] is None
    assert all(c["kappa"] is None and c["interpretation"] == "undefined" for c in body["criteria"])


def test_constant_scores_make_kappa_undefined(desk):
    client, rubric_id, _, tasks, other, rate = desk
    for task in tasks[:3]:
        rate(task, [2, 2])
        rate(task, [2, 2], other)
    body = agreement(client, rubric_id).json()
    assert body["shared_tasks"] == 3 and body["mean_kappa"] is None


def test_reviewer_names_are_normalised(desk):
    client, rubric_id, _, tasks, other, rate = desk
    rate(tasks[0], [1, 1])
    rate(tasks[0], [2, 2], other)
    assert agreement(client, rubric_id, " DR-A ", "Dr-B").json()["shared_tasks"] == 1


def test_validation_and_errors(desk):
    client, rubric_id, *_ = desk
    assert agreement(client, rubric_id, "dr-a", "DR-A ").status_code == 422
    assert agreement(client, 999).status_code == 404
    assert client.get(f"/rubrics/{rubric_id}/agreement").status_code == 422
    assert agreement(client, rubric_id, "x", "").status_code == 422


def test_agreement_requires_sign_in(anonymous):
    assert anonymous.get("/rubrics/1/agreement?reviewer_a=a&reviewer_b=b").status_code == 401
