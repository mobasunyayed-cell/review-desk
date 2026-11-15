# Security policy

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting instead:
**Security tab, then "Report a vulnerability"**. You will get a first reply within a few days.

## What the application already does

- Passwords are hashed with scrypt and a per-user salt. Login errors are identical for unknown users and wrong passwords, and the response time is equalised.
- Access tokens are signed JWTs (HS256) that expire (default 60 minutes). Without `REVIEW_DESK_SECRET_KEY` a random key is generated at start-up, so tokens stop working after a restart. Always set it in a real deployment (Docker Compose requires it).
- The reviewer name on a review always comes from the token, never from the request body.
- CSV exports neutralise spreadsheet formulas (CSV injection).
- The Docker image runs as a non-root user and contains no build tools or git.

## Scope notes

review-desk is a learning and portfolio project, not a certified system. Do not store
patient-identifiable information in it. There is no rate limiting or account lockout yet;
put it behind a reverse proxy that provides them before exposing it to the internet.
