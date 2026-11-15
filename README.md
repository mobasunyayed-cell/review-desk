# review-desk

[![CI](https://github.com/mobasunyayed-cell/review-desk/actions/workflows/ci.yml/badge.svg)](https://github.com/mobasunyayed-cell/review-desk/actions/workflows/ci.yml)

Web app for reviewing AI responses with rubric scoring and inter-reviewer agreement, built with FastAPI and SQLAlchemy. It is the companion to [medeval](https://github.com/mobasunyayed-cell/medeval): medeval evaluates models automatically, review-desk is where people review responses.

> Work in progress. See the roadmap below.

## Run it

```bash
pip install -e ".[dev]"
uvicorn review_desk.main:create_app --factory --reload
```

Open http://127.0.0.1:8000/docs for the interactive API documentation. The database defaults to a local SQLite file; set `REVIEW_DESK_DATABASE_URL` to change it.

## Authentication

Every endpoint except `/health`, `/auth/register` and `/auth/login` needs a bearer token.

```bash
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"username": "dr-ahmed", "password": "a long passphrase"}'
curl -X POST localhost:8000/auth/login -H 'content-type: application/json' \
  -d '{"username": "dr-ahmed", "password": "a long passphrase"}'
# then send:  Authorization: Bearer <access_token>
```

In the interactive docs use the **Authorize** button and paste the token. Passwords are hashed with scrypt and never returned. A review's reviewer is always the signed-in user, never a field the client can set.

| Variable | Default | Meaning |
|---|---|---|
| `REVIEW_DESK_SECRET_KEY` | random per start | Signs tokens. **Set it in any real deployment**, otherwise tokens stop working on restart. |
| `REVIEW_DESK_TOKEN_MINUTES` | `60` | Token lifetime |
| `REVIEW_DESK_ALLOW_REGISTRATION` | `true` | Set `false` to close sign-up once your reviewers exist |
| `REVIEW_DESK_DATABASE_URL` | local SQLite file | Database |

Known limits for now: no rate limiting on login and no password reset.

## API so far

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness and version (public) |
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Get an access token |
| GET | `/auth/me` | The signed-in user |
| POST | `/tasks` | Add an AI response to review (title, prompt, ai_response) |
| GET | `/tasks` | List tasks, filter by `status`, paginate with `limit` and `offset` |
| GET | `/tasks/{id}` | One task |
| POST | `/rubrics` | Create a rubric with weighted criteria (each with a max score) |
| GET | `/rubrics`, `/rubrics/{id}` | List or fetch rubrics |
| POST | `/tasks/{id}/reviews` | Score a task against a rubric |
| GET | `/tasks/{id}/reviews` | All reviews of a task |

A review must score every criterion of its rubric exactly once, within each criterion's maximum. The `total` is a weighted average from 0 to 1, with every score first scaled to its own maximum. A reviewer can review a task only once, and a task becomes `reviewed` after its first review.

## Roadmap

- [x] Project scaffold, tasks API, tests, CI
- [x] Rubrics and reviews with weighted scores
- [x] Reviewer accounts and authentication
- [ ] Inter-reviewer agreement (Cohen's kappa via medeval)
- [ ] Alembic migrations, PostgreSQL, Docker Compose
- [ ] Export of results

## Development

```bash
ruff check . && ruff format --check .
mypy
pytest --cov=review_desk
```

## AI assistance disclosure

Built with help from Claude (Anthropic) for code and guidance. I run the tests and I am responsible for the project.

## License

MIT, see [LICENSE](LICENSE).
