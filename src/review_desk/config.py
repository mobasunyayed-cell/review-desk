"""Settings read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./review_desk.db"
    secret_key: str | None = None
    token_minutes: int = 60
    allow_registration: bool = True
    auto_create_tables: bool = True


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def get_settings() -> Settings:
    defaults = Settings()
    return Settings(
        database_url=os.environ.get("REVIEW_DESK_DATABASE_URL", defaults.database_url),
        secret_key=os.environ.get("REVIEW_DESK_SECRET_KEY") or None,
        token_minutes=int(os.environ.get("REVIEW_DESK_TOKEN_MINUTES", defaults.token_minutes)),
        allow_registration=_flag("REVIEW_DESK_ALLOW_REGISTRATION", defaults.allow_registration),
        auto_create_tables=_flag("REVIEW_DESK_AUTO_CREATE_TABLES", defaults.auto_create_tables),
    )
