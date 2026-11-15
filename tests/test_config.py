import pytest

from review_desk.config import get_settings

VARIABLES = [
    "REVIEW_DESK_DATABASE_URL",
    "REVIEW_DESK_SECRET_KEY",
    "REVIEW_DESK_TOKEN_MINUTES",
    "REVIEW_DESK_ALLOW_REGISTRATION",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_defaults():
    settings = get_settings()
    assert settings.database_url.startswith("sqlite:///")
    assert settings.secret_key is None
    assert settings.token_minutes == 60 and settings.allow_registration is True


def test_values_from_environment(monkeypatch):
    monkeypatch.setenv("REVIEW_DESK_DATABASE_URL", "sqlite://")
    monkeypatch.setenv("REVIEW_DESK_SECRET_KEY", "s3cret")
    monkeypatch.setenv("REVIEW_DESK_TOKEN_MINUTES", "15")
    monkeypatch.setenv("REVIEW_DESK_ALLOW_REGISTRATION", "false")
    settings = get_settings()
    assert settings.database_url == "sqlite://" and settings.secret_key == "s3cret"
    assert settings.token_minutes == 15 and settings.allow_registration is False
