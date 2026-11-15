# Contributing

1. Fork the repository and create a branch: `git switch -c feature/short-name`.
2. Install the development tools: `pip install -e ".[dev]"`. Optionally run `pre-commit install`.
3. Make your change and add or update tests.
4. Run the same checks as CI:
   ```bash
   ruff check . && ruff format --check .
   mypy
   pytest --cov=review_desk --cov-fail-under=90
   ```
5. Open a pull request that says what changed and why.

## Ground rules

- **Changing `models.py` means adding a migration:** `alembic revision --autogenerate -m "what changed"`, then read the generated file. A test applies all migrations to an empty database and fails if the result differs from the models.
- Every endpoint except `/health`, `/auth/register` and `/auth/login` requires a bearer token.
- Never log or return password hashes or tokens. Text exported to CSV goes through `safe_cell`.
- Arithmetic that is not tied to the database (scores, agreement) lives in small pure functions with tests.
