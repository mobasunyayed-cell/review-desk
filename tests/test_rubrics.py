import pytest

RUBRIC = {
    "name": "Medical accuracy",
    "description": "Check facts and safety",
    "criteria": [
        {"name": "Accuracy", "weight": 3, "max_score": 5},
        {"name": "Safety", "weight": 2, "max_score": 5},
    ],
}


def test_create_and_get_rubric(client):
    response = client.post("/rubrics", json=RUBRIC)
    assert response.status_code == 201
    body = response.json()
    assert [c["name"] for c in body["criteria"]] == ["Accuracy", "Safety"]
    assert all("id" in c for c in body["criteria"])
    assert client.get(f"/rubrics/{body['id']}").json() == body
    assert client.get("/rubrics").json() == [body]


def test_criteria_defaults(client):
    body = client.post("/rubrics", json={"name": "R", "criteria": [{"name": "Clarity"}]}).json()
    assert body["criteria"][0]["weight"] == 1.0 and body["criteria"][0]["max_score"] == 5
    assert body["description"] == ""


def test_duplicate_rubric_name_conflicts(client):
    client.post("/rubrics", json=RUBRIC)
    assert client.post("/rubrics", json=RUBRIC).status_code == 409


def test_unknown_rubric_is_404(client):
    assert client.get("/rubrics/42").status_code == 404


@pytest.mark.parametrize(
    "criteria",
    [
        [],
        [{"name": ""}],
        [{"name": "A", "weight": 0}],
        [{"name": "A", "weight": 101}],
        [{"name": "A", "max_score": 0}],
        [{"name": "A", "max_score": 11}],
        [{"name": "A"}, {"name": "a"}],  # names are unique ignoring case
    ],
)
def test_invalid_rubrics_are_rejected(client, criteria):
    assert client.post("/rubrics", json={"name": "R", "criteria": criteria}).status_code == 422
