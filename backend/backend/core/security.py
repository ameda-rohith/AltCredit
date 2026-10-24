"""Password hashing and signed access tokens (stdlib only), plus anonymous lead ids."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from functools import lru_cache

from core.config import settings

HASH_SCHEME = "pbkdf2_sha256"
# Hashes written before the scheme/iterations were stored had the form "<salt>$<hex>"
# and always used this iteration count.
LEGACY_ITERATIONS = 200_000


def _digest(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    """`pbkdf2_sha256$<iterations>$<salt>$<hex>`: the cost travels with the hash."""
    salt = secrets.token_hex(16)
    iterations = settings.pbkdf2_iterations
    return f"{HASH_SCHEME}${iterations}${salt}${_digest(password, salt, iterations)}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == HASH_SCHEME and parts[1].isdigit():
        return int(parts[1]), parts[2], parts[3]
    if len(parts) == 2:  # legacy "<salt>$<hex>"
        return LEGACY_ITERATIONS, parts[0], parts[1]
    return None


def verify_password(password: str, stored: str | None) -> bool:
    parsed = _parse(stored) if stored else None
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    return hmac.compare_digest(_digest(password, salt, iterations), expected)


def needs_rehash(stored: str | None) -> bool:
    """True for legacy hashes and hashes made with fewer iterations than configured."""
    parsed = _parse(stored) if stored else None
    if parsed is None:  # unusable anyway; nothing to upgrade
        return False
    return not stored.startswith(f"{HASH_SCHEME}$") or parsed[0] < settings.pbkdf2_iterations


@lru_cache
def dummy_hash() -> str:
    """Verified against when the account does not exist, so unknown users cost the same time."""
    return hash_password(secrets.token_hex(8))


# --- access tokens ---------------------------------------------------------------------
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str) -> str:
    return _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())


def create_token(subject: str, role: str, ttl_minutes: int | None = None) -> str:
    ttl = settings.token_ttl_minutes if ttl_minutes is None else ttl_minutes
    payload = {"sub": subject, "role": role, "exp": int(time.time()) + ttl * 60}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body)}"


def decode_token(token: str) -> dict | None:
    """The verified payload, or None for anything malformed, tampered with or expired."""
    try:
        body, signature = token.split(".")
        if not hmac.compare_digest(_sign(body), signature):
            return None
        payload = json.loads(_unb64(body))
    except (ValueError, TypeError):
        return None
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("sub"), str)
        or payload.get("role") not in ("user", "lender")
        or not isinstance(payload.get("exp"), int)
        or payload["exp"] < time.time()
    ):
        return None
    return payload


def new_anon_id(existing: set[str]) -> str:
    while True:
        candidate = f"ANON-{secrets.token_hex(3).upper()}"
        if candidate not in existing:
            return candidate
