import pytest

from app.api.routes import explain as explain_route
from core.config import settings
from services import llm_explainer

API = settings.api_prefix
NARRATIVE = {"model": "m", "summary": "s", "strengths": [], "weaknesses": [], "next_steps": []}


@pytest.fixture
def llm(monkeypatch):
    """A counting stand-in for the paid model, with a clean cache and budget per test."""
    calls = []
    monkeypatch.setattr(settings, "ollama_api_key", "test-key")

    def fake(scored, client=None):
        calls.append(scored["credit_score"])
        return dict(NARRATIVE)

    monkeypatch.setattr(llm_explainer, "explain_score", fake)
    explain_route.explain_cache.clear()
    explain_route.explain_limiter.reset("USR_005")
    yield calls
    explain_route.explain_cache.clear()
    explain_route.explain_limiter.reset("USR_005")


def test_unchanged_score_is_served_from_cache(client, login_as, llm):
    login_as("USR_005")
    first = client.get(f"{API}/scoring/USR_005/explain")
    second = client.get(f"{API}/scoring/USR_005/explain")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() and len(llm) == 1


def test_changed_score_inputs_regenerate(client, login_as, llm):
    login_as("USR_005")
    client.get(f"{API}/scoring/USR_005/explain")
    client.put(f"{API}/scoring/USR_005/profile", json={"on_time_rate": 0.1})
    client.get(f"{API}/scoring/USR_005/explain")
    assert len(llm) == 2


def test_fresh_generations_are_rate_limited_but_cache_hits_are_free(
    client, login_as, llm, monkeypatch
):
    monkeypatch.setattr(explain_route.explain_limiter, "limit", 2)
    login_as("USR_005")
    for on_time in (0.2, 0.4):  # two different inputs -> two fresh generations
        client.put(f"{API}/scoring/USR_005/profile", json={"on_time_rate": on_time})
        assert client.get(f"{API}/scoring/USR_005/explain").status_code == 200
    assert client.get(f"{API}/scoring/USR_005/explain").status_code == 200  # cached: free
    client.put(f"{API}/scoring/USR_005/profile", json={"on_time_rate": 0.99})
    blocked = client.get(f"{API}/scoring/USR_005/explain")
    assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) >= 1
    assert len(llm) == 2


def test_missing_key_is_503_and_does_not_burn_the_budget(client, login_as, monkeypatch):
    monkeypatch.setattr(settings, "ollama_api_key", "")
    explain_route.explain_cache.clear()
    explain_route.explain_limiter.reset("USR_006")
    login_as("USR_006")
    assert client.get(f"{API}/scoring/USR_006/explain").status_code == 503
    assert explain_route.explain_limiter.retry_after("USR_006") == 1  # nothing recorded
