from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from conftest import SECRET, sign_in
from review_desk.db import make_engine
from review_desk.main import create_app
from review_desk.models import Task


def test_file_database_persists_between_app_instances(tmp_path):
    url = f"sqlite:///{tmp_path / 'desk.db'}"
    payload = {"title": "t", "prompt": "p", "ai_response": "r"}
    first = create_app(url, secret_key=SECRET)
    with TestClient(first) as client:
        client.headers.update(sign_in(client, "dr-a"))
        assert client.post("/tasks", json=payload).status_code == 201
    first.state.engine.dispose()

    second = create_app(url, secret_key=SECRET)
    with TestClient(second) as client:
        client.headers.update(sign_in(client, "dr-a"))  # the user survived the restart
        assert len(client.get("/tasks").json()) == 1
    second.state.engine.dispose()


def test_datetimes_round_trip_as_utc():
    engine = make_engine("sqlite://")
    create_app("sqlite://").state.engine.dispose()
    from review_desk.db import Base

    Base.metadata.create_all(engine)
    cairo = timezone(timedelta(hours=2))
    stamp = datetime(2026, 11, 14, 12, 0, tzinfo=cairo)
    with Session(engine) as session:
        session.add(Task(title="t", prompt="p", ai_response="r", created_at=stamp))
        session.commit()
        loaded = session.scalars(select(Task)).one().created_at
    assert loaded == stamp
    assert loaded.utcoffset() == timedelta(0)
    engine.dispose()


def test_naive_datetimes_are_rejected():
    engine = make_engine("sqlite://")
    from review_desk.db import Base

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Task(title="t", prompt="p", ai_response="r", created_at=datetime(2026, 1, 1)))
        with pytest.raises(StatementError, match="naive datetime"):
            session.commit()
    engine.dispose()
