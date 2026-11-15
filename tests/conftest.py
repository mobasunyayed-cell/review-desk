from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from review_desk.main import create_app

PASSWORD = "correct horse battery"
SECRET = "test-secret-key-that-is-long-enough-for-hs256"


def sign_in(client: TestClient, username: str) -> dict[str, str]:
    """Register (if needed) and log in; returns headers for authenticated requests."""
    client.post("/auth/register", json={"username": username, "password": PASSWORD})
    token = client.post("/auth/login", json={"username": username, "password": PASSWORD})
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


@pytest.fixture
def app() -> Iterator[FastAPI]:
    application = create_app("sqlite://", secret_key=SECRET)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def anonymous(app: FastAPI) -> Iterator[TestClient]:
    """A client with no credentials."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """A client already signed in as 'dr-a'."""
    with TestClient(app) as test_client:
        test_client.headers.update(sign_in(test_client, "dr-a"))
        yield test_client
