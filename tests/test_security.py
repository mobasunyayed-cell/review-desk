from datetime import datetime, timedelta, timezone

import pytest

from review_desk.security import (
    create_token,
    decode_token,
    dummy_hash,
    hash_password,
    verify_password,
)

SECRET = "unit-test-secret-key-with-enough-length"


def test_hash_verifies_and_is_salted():
    first, second = hash_password("a long password"), hash_password("a long password")
    assert first != second
    assert verify_password("a long password", first) and verify_password("a long password", second)
    assert not verify_password("a long passworD", first)


def test_unicode_passwords_work():
    stored = hash_password("كلمة سر طويلة جداً")
    assert verify_password("كلمة سر طويلة جداً", stored)


@pytest.mark.parametrize(
    "stored", ["", "plain", "scrypt$1$2", "md5$1$1$1$aa$bb", "scrypt$x$8$1$aa$bb"]
)
def test_malformed_stored_hashes_fail_closed(stored):
    assert verify_password("anything", stored) is False


def test_dummy_hash_is_valid_but_matches_nothing_real():
    assert dummy_hash() == dummy_hash()
    assert not verify_password("hunter2hunter2", dummy_hash())


def test_token_round_trip_and_expiry():
    token = create_token("dr-a", SECRET, 5)
    assert decode_token(token, SECRET) == "dr-a"
    old = datetime.now(timezone.utc) - timedelta(minutes=10)
    assert decode_token(create_token("dr-a", SECRET, 5, now=old), SECRET) is None


def test_token_rejects_other_secret_and_garbage():
    token = create_token("dr-a", SECRET, 5)
    assert decode_token(token, "different-secret-key-with-enough-length") is None
    assert decode_token("x.y.z", SECRET) is None
