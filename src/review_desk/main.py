"""Application factory."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from review_desk import __version__
from review_desk.api import reviews, rubrics, tasks
from review_desk.config import get_settings
from review_desk.db import Base, make_engine


def create_app(database_url: str | None = None) -> FastAPI:
    """Build the app. Tests pass an in-memory database URL.

    Run with: uvicorn review_desk.main:create_app --factory
    """
    engine = make_engine(database_url or get_settings().database_url)
    Base.metadata.create_all(engine)  # replaced by Alembic migrations in a later step

    app = FastAPI(title="review-desk", version=__version__)
    app.state.engine = engine
    app.state.session_factory = sessionmaker(engine, expire_on_commit=False)
    app.include_router(tasks.router)
    app.include_router(rubrics.router)
    app.include_router(reviews.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app
