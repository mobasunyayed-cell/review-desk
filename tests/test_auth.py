from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from conftest import PASSWORD, SECRET, sign_in
from review_desk.main import create_app
from review_desk.security import create_token


def register(client, username="dr-a", password=PASSWORD):
    return client.post("/auth/register", json={"username": username, "password": password})


def test_register_returns_user_without_password(anonymous):
    response = register(anonymous, "  Dr.Ahmed  ")
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "dr.ahmed" and "password" not in body and "password_hash" not in body


def test_duplicate_username_conflicts_ignoring_case(anonymous):
    register(anonymous, "dr-a")
    assert register(anonymous, "DR-A").status_code == 409


@pytest.mark.parametrize("username", ["ab", "has space", "x" * 51, "bad/char", ""])
def test_invalid_usernames_rejected(anonymous, username):
    assert register(anonymous, username).status_code == 422


@pytest.mark.parametrize("password", ["short", "x" * 9, "x" * 129])
def test_invalid_passwords_rejected(anonymous, password):
    assert register(anonymous, "dr-a", password).status_code == 422


def test_registration_can_be_disabled():
    app = create_app("sqlite://", secret_key=SECRET, allow_registration=False)
    with TestClient(app) as client:
        assert register(client).status_code == 403
    app.state.engine.dispose()


def test_login_token_works_on_me(anonymous):
    register(anonymous)
    login = anonymous.post("/auth/login", json={"username": "DR-A", "password": PASSWORD})
    assert login.status_code == 200 and login.json()["token_type"] == "bearer"
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = anonymous.get("/auth/me", headers=headers)
    assert me.json()["username"] == "dr-a"


def test_wrong_password_and_unknown_user_look_the_same(anonymous):
    register(anonymous)
    wrong = anonymous.post("/auth/login", json={"username": "dr-a", "password": "nope-nope-nope"})
    unknown = anonymous.post("/auth/login", json={"username": "ghost", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.headers["www-authenticate"] == "Bearer"


PROTECTED = [
    ("get", "/auth/me"),
    ("get", "/tasks"),
    ("post", "/tasks"),
    ("get", "/tasks/1"),
    ("get", "/rubrics"),
    ("post", "/rubrics"),
    ("get", "/rubrics/1"),
    ("get", "/tasks/1/reviews"),
    ("post", "/tasks/1/reviews"),
]


@pytest.mark.parametrize("method, path", PROTECTED)
def test_endpoints_require_authentication(anonymous, method, path):
    response = getattr(anonymous, method)(path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_health_and_docs_stay_public(anonymous):
    assert anonymous.get("/health").status_code == 200
    assert anonymous.get("/docs").status_code == 200


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_garbage_expired_and_foreign_tokens_are_rejected(anonymous):
    sign_in(anonymous, "dr-a")
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    cases = {
        "garbage": "not-a-token",
        "expired": create_token("dr-a", SECRET, 60, now=past),
        "wrong secret": create_token("dr-a", "another-secret-key-of-sufficient-length", 60),
        "unknown user": create_token("ghost", SECRET, 60),
    }
    for name, token in cases.items():
        response = anonymous.get("/auth/me", headers=bearer(token))
        assert response.status_code == 401, name


def test_token_without_bearer_scheme_is_rejected(anonymous):
    token = sign_in(anonymous, "dr-a")["Authorization"].split()[1]
    assert anonymous.get("/auth/me", headers={"Authorization": token}).status_code == 401
