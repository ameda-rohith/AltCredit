import json

import httpx
import pytest

from core.config import settings
from services import llm_explainer

SCORED = {
    "credit_score": 665,
    "max_score": 1000,
    "risk_tier": "Near-Prime / Medium Risk",
    "pillar_breakdown": {"lifestyle": 300},
    "explanation": {
        "all_factors": [
            {
                "factor": "Employment Stability",
                "pillar": "Lifestyle",
                "score": 150,
                "max_score": 150,
                "value": 30,
            }
        ]
    },
}
GOOD = {"summary": "s", "strengths": ["a"], "weaknesses": ["b"], "next_steps": ["c", "d", "e", "f"]}


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_explain_score_sends_methodology_and_parses(monkeypatch):
    monkeypatch.setattr(settings, "ollama_api_key", "k")
    seen = {}

    def handler(req):
        seen["auth"] = req.headers["authorization"]
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"message": {"content": json.dumps(GOOD)}})

    out = llm_explainer.explain_score(SCORED, _client(handler))
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "gpt-oss:120b"
    assert "METHODOLOGY" in seen["body"]["messages"][0]["content"]
    assert json.loads(seen["body"]["messages"][1]["content"])["credit_score"] == 665
    assert out["summary"] == "s" and len(out["next_steps"]) == 3


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "ollama_api_key", "")
    with pytest.raises(llm_explainer.LLMUnavailable):
        llm_explainer.explain_score(SCORED)


@pytest.mark.parametrize(
    "resp",
    [httpx.Response(500), httpx.Response(200, json={"message": {"content": "not json"}})],
)
def test_bad_upstream_raises(monkeypatch, resp):
    monkeypatch.setattr(settings, "ollama_api_key", "k")
    with pytest.raises(llm_explainer.LLMUnavailable):
        llm_explainer.explain_score(SCORED, _client(lambda req: resp))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, []),
        ("one tip", ["one tip"]),  # a lone string is one item, not a list of characters
        (["a", None, "", "  ", "b"], ["a", "b"]),
        ([1, 2, 3, 4, 5], ["1", "2", "3"]),
        ({"a": 1}, []),
        (["x" * 1000], ["x" * 400]),
    ],
)
def test_list_fields_are_coerced_not_crashed_on(raw, expected):
    out = llm_explainer._parse(json.dumps({"summary": "s", "strengths": raw}))
    assert out["strengths"] == expected and out["weaknesses"] == [] and out["next_steps"] == []


def test_non_text_model_content_is_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "ollama_api_key", "k")
    for body in ({"message": None}, {"message": {"content": 5}}, {"message": {"content": None}}):
        with pytest.raises(llm_explainer.LLMUnavailable):
            llm_explainer.explain_score(
                SCORED, _client(lambda req, body=body: httpx.Response(200, json=body))
            )


def test_cache_key_tracks_user_and_prompt_inputs():
    key = llm_explainer.ExplanationCache.key
    assert key("USR_1", SCORED) == key("USR_1", dict(SCORED))
    assert key("USR_1", SCORED) != key("USR_2", SCORED)
    assert key("USR_1", SCORED) != key("USR_1", {**SCORED, "credit_score": 666})


def test_cache_expires_and_is_bounded():
    now = [0.0]
    cache = llm_explainer.ExplanationCache(10, max_entries=2, clock=lambda: now[0])
    cache.set("a", {"n": 1})
    assert cache.get("a") == {"n": 1}
    now[0] = 11
    assert cache.get("a") is None
    cache.set("a", {"n": 1})
    cache.set("b", {"n": 2})
    cache.set("c", {"n": 3})  # evicts the oldest
    assert cache.get("a") is None and cache.get("c") == {"n": 3}
