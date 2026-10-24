import hashlib

from sqlalchemy import select

from app import models
from core import security
from core.config import settings
from core.database import SessionLocal

API = settings.api_prefix


def test_new_hashes_carry_scheme_and_cost():
    h = security.hash_password("s3cret-pass")
    scheme, iterations, salt, digest = h.split("$")
    assert scheme == "pbkdf2_sha256" and int(iterations) == settings.pbkdf2_iterations
    assert security.verify_password("s3cret-pass", h)
    assert not security.verify_password("s3cret-pasS", h)
    assert security.hash_password("s3cret-pass") != h  # fresh salt every time
    assert not security.needs_rehash(h)


def _legacy(password: str, salt: str = "abc123") -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def test_legacy_hashes_still_verify_and_are_flagged():
    legacy = _legacy("old-password")
    assert security.verify_password("old-password", legacy)
    assert not security.verify_password("other", legacy)
    assert security.needs_rehash(legacy)


def test_malformed_hashes_never_verify():
    for stored in (None, "", "nodollar", "a$b$c", "pbkdf2_sha256$x$salt$hex", "pbkdf2_sha256$1$s"):
        assert not security.verify_password("anything", stored)


def test_lower_cost_hashes_are_flagged(monkeypatch):
    h = security.hash_password("pw")
    monkeypatch.setattr(settings, "pbkdf2_iterations", settings.pbkdf2_iterations + 1)
    assert security.needs_rehash(h)


def test_login_upgrades_a_legacy_hash(client):
    with SessionLocal() as db:
        user = db.scalar(select(models.User).where(models.User.user_id == "USR_010"))
        user.password_hash = _legacy("legacy-pass")
        db.commit()
    r = client.post(f"{API}/auth/login", json={"username": "USR_010", "password": "legacy-pass"})
    assert r.status_code == 200
    with SessionLocal() as db:
        stored = db.get(models.User, "USR_010").password_hash
    assert stored.startswith("pbkdf2_sha256$") and security.verify_password("legacy-pass", stored)


def test_tokens_round_trip_and_expire():
    token = security.create_token("USR_001", "user")
    assert security.decode_token(token)["sub"] == "USR_001"
    assert security.decode_token(security.create_token("1", "lender"))["role"] == "lender"
    assert security.decode_token(security.create_token("USR_001", "user", ttl_minutes=-1)) is None
    assert security.decode_token(security.create_token("USR_001", "admin")) is None


def test_blank_secret_key_never_becomes_an_empty_signing_key():
    from core.config import DEV_SECRET_KEY, Settings

    assert Settings(secret_key="").secret_key == DEV_SECRET_KEY
    assert Settings(secret_key="   ").secret_key == DEV_SECRET_KEY
    assert Settings(secret_key="real-key").secret_key == "real-key"
