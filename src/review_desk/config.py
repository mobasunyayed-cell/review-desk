"""Settings read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./review_desk.db"


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("REVIEW_DESK_DATABASE_URL", Settings.database_url),
    )
