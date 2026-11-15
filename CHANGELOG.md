# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-15

### Added
- FastAPI service for tasks, weighted rubrics and reviews, with SQLAlchemy 2.0 models.
- Registration, login and bearer-token (JWT) authentication; scrypt password hashing.
- Weighted scoring that scales each criterion to its own maximum.
- Inter-reviewer agreement per criterion (quadratic-weighted Cohen's kappa, via medeval).
- Alembic migrations with a test that fails when the models and migrations drift apart.
- Docker image, Docker Compose stack with PostgreSQL, and a CI smoke test that runs against PostgreSQL.
- CSV and JSON export of a rubric's reviews, protected against CSV injection.
- CodeQL scanning, Dependabot and a tag-driven release workflow.
