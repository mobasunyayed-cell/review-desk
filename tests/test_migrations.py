from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import review_desk.models  # noqa: F401
from review_desk.db import Base
from review_desk.main import create_app

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def alembic_config(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config, url


def test_migrations_produce_exactly_the_schema_the_models_declare(alembic_config):
    config, url = alembic_config
    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []
    engine.dispose()


def test_downgrade_removes_every_table(alembic_config):
    config, url = alembic_config
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    engine.dispose()


def test_postgres_sql_can_be_rendered_offline(alembic_config, capsys):
    config, _ = alembic_config
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://u:p@localhost/db")
    command.upgrade(config, "head", sql=True)
    sql = capsys.readouterr().out
    assert "CREATE TYPE taskstatus AS ENUM" in sql
    assert "CREATE TABLE reviews" in sql and "TIMESTAMP WITH TIME ZONE" in sql


def test_app_can_skip_table_creation_for_migrated_databases(tmp_path):
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    app = create_app(url, create_tables=False)
    assert inspect(app.state.engine).get_table_names() == []
    app.state.engine.dispose()
