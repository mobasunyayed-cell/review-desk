"""Password hashing and access tokens."""

from __future__ import annotations

import functools
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

_COST = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    """Hash with scrypt and a random salt. The cost is stored so it can be raised later."""
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, dklen=32, **_COST)
    return f"scrypt${_COST['n']}${_COST['r']}${_COST['p']}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check. Malformed stored values simply fail."""
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)


@functools.cache
def dummy_hash() -> str:
    """A valid hash to compare against when the user does not exist, so timing stays similar."""
    return hash_password("not-a-real-password")


def create_token(subject: str, secret: str, minutes: int, now: datetime | None = None) -> str:
    issued = now or datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": issued, "exp": issued + timedelta(minutes=minutes)}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> str | None:
    """Return the username in a valid, unexpired token, or None."""
    try:
        payload = jwt.decode(
            token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
