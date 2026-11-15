"""Application factory."""

from __future__ import annotations

import secrets

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from review_desk import __version__
from review_desk.api import auth, reviews, rubrics, tasks
from review_desk.config import get_settings
from review_desk.db import Base, make_engine


def create_app(
    database_url: str | None = None,
    *,
    secret_key: str | None = None,
    token_minutes: int | None = None,
    allow_registration: bool | None = None,
    create_tables: bool | None = None,
) -> FastAPI:
    """Build the app. Tests pass an in-memory database URL and a fixed secret.

    Without REVIEW_DESK_SECRET_KEY a random key is generated, so tokens stop working when the
    process restarts. Set the variable in any real deployment.

    Run with: uvicorn review_desk.main:create_app --factory
    """
    settings = get_settings()
    engine = make_engine(database_url or settings.database_url)
    if settings.auto_create_tables if create_tables is None else create_tables:
        # Convenient for development and tests. Deployments run `alembic upgrade head` instead.
        Base.metadata.create_all(engine)

    app = FastAPI(title="review-desk", version=__version__)
    app.state.engine = engine
    app.state.secret_key = secret_key or settings.secret_key or secrets.token_urlsafe(32)
    app.state.token_minutes = token_minutes or settings.token_minutes
    app.state.allow_registration = (
        settings.allow_registration if allow_registration is None else allow_registration
    )
    app.state.session_factory = sessionmaker(engine, expire_on_commit=False)
    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(rubrics.router)
    app.include_router(reviews.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app
