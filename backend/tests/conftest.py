import os
import tempfile
from pathlib import Path

# Must be set before the app imports its settings.
_tmp = tempfile.mkdtemp(prefix="altcredit-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["PBKDF2_ITERATIONS"] = "1000"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from bank_mock.main import app as bank_app  # noqa: E402
from core.config import settings  # noqa: E402
from services import bank_client  # noqa: E402

API = settings.api_prefix


@pytest.fixture(scope="session")
def client():
    # the "bank" runs in-process; same X-API-Key contract as over the network
    bank_client.get_client = lambda: TestClient(bank_app, base_url="http://bank")
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _anonymous(client):
    """Every test starts without credentials; log in explicitly with `login_as`."""
    client.headers.pop("Authorization", None)
    yield
    client.headers.pop("Authorization", None)


def _token_headers(client, username, role="user", password=None):
    r = client.post(
        f"{API}/auth/login",
        json={"username": username, "role": role, "password": password or settings.demo_password},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return body["subject"], {"Authorization": f"Bearer {body['token']}"}


@pytest.fixture
def login_as(client):
    """Log the shared client in (replacing any previous login); returns the subject id."""

    def _login(username, role="user"):
        subject, headers = _token_headers(client, username, role)
        client.headers.update(headers)
        return subject

    return _login


@pytest.fixture
def headers_for(client):
    """Authorization headers for one request, without touching the client's own login."""

    def _headers(username, role="user"):
        return _token_headers(client, username, role)[1]

    return _headers
