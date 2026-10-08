"""Shared-credential authentication helpers."""

from __future__ import annotations

import hashlib
import hmac


_PBKDF2_ITERATIONS = 600_000


def verify_credentials(
    username: str,
    password: str,
    configured_username: str,
    password_salt: str,
    password_hash: str,
) -> bool:
    """Verify a username and PBKDF2-SHA256 password hash."""
    try:
        salt = bytes.fromhex(password_salt)
        expected_hash = bytes.fromhex(password_hash)
    except ValueError:
        return False

    if len(salt) < 16 or len(expected_hash) != hashlib.sha256().digest_size:
        return False

    supplied_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    username_matches = hmac.compare_digest(
        username.encode("utf-8"),
        configured_username.encode("utf-8"),
    )
    password_matches = hmac.compare_digest(supplied_hash, expected_hash)
    return username_matches and password_matches
