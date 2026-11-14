"""Shared request dependencies."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from review_desk.models import User
from review_desk.security import decode_token


def get_session(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


def current_user(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """The signed-in user, or a 401. Every endpoint except register and login needs this."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    username = decode_token(credentials.credentials, request.app.state.secret_key)
    if username is None:
        raise unauthorized
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(current_user)]
