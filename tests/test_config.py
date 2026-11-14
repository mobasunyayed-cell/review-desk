from review_desk.config import get_settings


def test_default_database_url(monkeypatch):
    monkeypatch.delenv("REVIEW_DESK_DATABASE_URL", raising=False)
    assert get_settings().database_url.startswith("sqlite:///")


def test_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("REVIEW_DESK_DATABASE_URL", "sqlite://")
    assert get_settings().database_url == "sqlite://"
