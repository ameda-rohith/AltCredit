import pytest

from app.api.routes.auth import login_failures
from core import security
from core.config import settings

API = settings.api_prefix

USER_ROUTES = [
    ("get", "/scoring/USR_001"),
    ("get", "/scoring/USR_001/history"),
    ("get", "/scoring/USR_001/export.json"),
    ("get", "/scoring/USR_001/report.pdf"),
    ("get", "/scoring/USR_001/explain"),
    ("get", "/scoring/USR_001/target?product_id=P_01"),
    ("get", "/dashboard/USR_001"),
    ("get", "/products/USR_001/recommendations"),
    ("get", "/products/USR_001/offers"),
    ("put", "/scoring/USR_001/profile"),
    ("post", "/scoring/USR_001/what-if"),
    ("post", "/products/USR_001/apply"),
    ("post", "/products/USR_001/offers/1/respond"),
]
LENDER_ROUTES = [
    ("get", "/lender/1"),
    ("get", "/lender/1/candidates"),
    ("get", "/lender/1/candidates/ANON-AAAAAA"),
    ("get", "/lender/1/offers"),
    ("post", "/lender/1/offers"),
]


def _call(client, method, path):
    kwargs = {"json": {}} if method in ("post", "put") else {}
    return getattr(client, method)(f"{API}{path}", **kwargs)


@pytest.mark.parametrize(("method", "path"), USER_ROUTES + LENDER_ROUTES)
def test_protected_routes_require_a_token(client, method, path):
    r = _call(client, method, path)
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"


def test_public_routes_stay_open(client):
    assert client.get("/health").status_code == 200
    assert client.get(f"{API}/products").status_code == 200


@pytest.mark.parametrize(("method", "path"), USER_ROUTES)
def test_user_cannot_touch_another_users_data(client, login_as, method, path):
    login_as("USR_002")
    assert _call(client, method, path).status_code == 403


@pytest.mark.parametrize(("method", "path"), LENDER_ROUTES)
def test_lender_routes_reject_other_lenders_and_users(client, login_as, method, path):
    login_as("USR_002")
    assert _call(client, method, path).status_code == 403  # a borrower
    login_as("microfin", "lender")  # lender 2 against lender 1's routes
    assert _call(client, method, path).status_code == 403


def test_user_routes_reject_lender_tokens(client, login_as):
    login_as("primebank", "lender")
    assert client.get(f"{API}/scoring/USR_001").status_code == 403


def test_bad_tokens_are_rejected(client):
    good = security.create_token("USR_001", "user")
    body, sig = good.split(".")
    flipped = ("A" if sig[0] != "A" else "B") + sig[1:]
    forged = security.create_token("USR_001", "user").split(".")[0]
    for token in (
        "garbage",
        "",
        f"{body}.{flipped}",  # tampered signature
        f"{forged}.",  # unsigned
        security.create_token("USR_001", "user", ttl_minutes=-1),  # expired
    ):
        r = client.get(f"{API}/scoring/USR_001", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401, token
    # the same request with the untouched token works
    ok = client.get(f"{API}/scoring/USR_001", headers={"Authorization": f"Bearer {good}"})
    assert ok.status_code == 200


def test_token_signed_with_another_key_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "someone-elses-key")
    foreign = security.create_token("USR_001", "user")
    monkeypatch.undo()
    r = client.get(f"{API}/scoring/USR_001", headers={"Authorization": f"Bearer {foreign}"})
    assert r.status_code == 401


def test_register_endpoints_return_a_working_token(client):
    reg = client.post(
        f"{API}/auth/register",
        json={"full_name": "Tok En", "email": "token.user@example.test", "password": "longenough1"},
    ).json()
    h = {"Authorization": f"Bearer {reg['token']}"}
    assert client.get(f"{API}/scoring/{reg['user_id']}", headers=h).status_code == 200
    lender = client.post(
        f"{API}/auth/register-lender",
        json={"company_name": "Token Bank", "username": "tokenbank", "password": "longenough1"},
    ).json()
    h = {"Authorization": f"Bearer {lender['token']}"}
    assert client.get(f"{API}/lender/{lender['subject']}", headers=h).status_code == 200


def test_unknown_account_is_verified_like_a_wrong_password(client, monkeypatch):
    calls = []
    real = security.verify_password
    monkeypatch.setattr(
        security, "verify_password", lambda pw, stored: calls.append(stored) or real(pw, stored)
    )
    for username in ("nobody-here", "USR_001"):
        r = client.post(f"{API}/auth/login", json={"username": username, "password": "wrong-pw"})
        assert r.status_code == 401 and r.json()["detail"] == "invalid credentials"
    assert len(calls) == 2 and calls[0] == security.dummy_hash()  # work done for both


def test_repeated_failed_logins_are_throttled_and_success_resets(client):
    name = "throttle-target"
    bad = {"username": name, "password": "wrong-pw"}
    for _ in range(settings.login_max_failures):
        assert client.post(f"{API}/auth/login", json=bad).status_code == 401
    blocked = client.post(f"{API}/auth/login", json=bad)
    assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) >= 1
    # other accounts are unaffected, and a real login clears its own counter
    assert (
        client.post(
            f"{API}/auth/login", json={"username": "USR_003", "password": settings.demo_password}
        ).status_code
        == 200
    )
    for _ in range(3):
        client.post(f"{API}/auth/login", json={"username": "USR_004", "password": "nope"})
    ok = client.post(
        f"{API}/auth/login", json={"username": "USR_004", "password": settings.demo_password}
    )
    assert ok.status_code == 200
    assert not login_failures.blocked("user:usr_004:testclient")
    login_failures.reset(f"user:{name}:testclient")
