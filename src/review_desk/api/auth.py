"""Registration, login and the current user."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from review_desk.api.deps import CurrentUser, SessionDep
from review_desk.models import User
from review_desk.schemas import LoginIn, TokenOut, UserCreate, UserOut
from review_desk.security import create_token, dummy_hash, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, session: SessionDep) -> User:
    if not request.app.state.allow_registration:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "registration is disabled")
    taken = HTTPException(status.HTTP_409_CONFLICT, "username already taken")
    if session.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise taken
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:  # pragma: no cover - only when two requests race for one name
        session.rollback()
        raise taken from None
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, session: SessionDep) -> TokenOut:
    user = session.scalar(select(User).where(User.username == payload.username))
    # Always verify something, so an unknown user costs the same time as a wrong password.
    valid = verify_password(payload.password, user.password_hash if user else dummy_hash())
    if user is None or not valid:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token(
        user.username, request.app.state.secret_key, request.app.state.token_minutes
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
