import pytest

PAYLOAD = {"title": "Aspirin dose", "prompt": "What is the dose?", "ai_response": "It depends."}


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["version"]


def test_create_task_starts_pending(client):
    response = client.post("/tasks", json=PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1 and body["status"] == "pending"
    assert body["title"] == "Aspirin dose" and body["created_at"]


def test_create_strips_whitespace(client):
    response = client.post("/tasks", json={**PAYLOAD, "title": "  padded  "})
    assert response.json()["title"] == "padded"


@pytest.mark.parametrize(
    "patch",
    [{"title": ""}, {"title": "   "}, {"prompt": ""}, {"ai_response": ""}, {"title": "x" * 201}],
)
def test_create_rejects_invalid_input(client, patch):
    assert client.post("/tasks", json={**PAYLOAD, **patch}).status_code == 422


def test_create_rejects_missing_fields(client):
    assert client.post("/tasks", json={"title": "only a title"}).status_code == 422


def test_get_task_and_404(client):
    created = client.post("/tasks", json=PAYLOAD).json()
    assert client.get(f"/tasks/{created['id']}").json() == created
    assert client.get("/tasks/999").status_code == 404
    assert client.get("/tasks/not-a-number").status_code == 422


def test_list_orders_by_id_and_paginates(client):
    for i in range(5):
        client.post("/tasks", json={**PAYLOAD, "title": f"task {i}"})
    ids = [t["id"] for t in client.get("/tasks").json()]
    assert ids == [1, 2, 3, 4, 5]
    page = client.get("/tasks", params={"limit": 2, "offset": 2}).json()
    assert [t["id"] for t in page] == [3, 4]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 201}, {"offset": -1}, {"status": "x"}])
def test_list_validates_query(client, params):
    assert client.get("/tasks", params=params).status_code == 422


def test_list_filters_by_status(client):
    client.post("/tasks", json=PAYLOAD)
    assert len(client.get("/tasks", params={"status": "pending"}).json()) == 1
    assert client.get("/tasks", params={"status": "reviewed"}).json() == []
