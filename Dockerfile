# Build stage: git is needed only to fetch medeval from its GitHub tag.
FROM python:3.15-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --no-cache-dir --wheel-dir /wheels ".[postgres]"

# Runtime stage: no git, no build tools, non-root user.
FROM python:3.15-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index --no-deps /wheels/*.whl && pip check && rm -rf /wheels
COPY alembic.ini ./
COPY migrations ./migrations
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn review_desk.main:create_app --factory --host 0.0.0.0 --port 8000"]
