import pytest

from core.config import settings
from services import data_parser, report_service, user_service

API = settings.api_prefix


def _what_if(client, body):
    return client.post(f"{API}/scoring/USR_002/what-if", json=body)


def test_education_is_normalised_and_arbitrary_text_rejected(client, login_as):
    login_as("USR_007")
    url = f"{API}/scoring/USR_007/profile"
    assert client.put(url, json={"education_level": "bachelor"}).status_code == 200
    assert (
        client.get(f"{API}/scoring/USR_007/export.json").json()["input_profile"]["education_level"]
        == "Bachelor's"
    )
    for bad in ("<b>x", "x" * 100_000, "Astronaut", ""):
        assert client.put(url, json={"education_level": bad}).status_code == 422, bad[:20]


def test_below_high_school_scores_zero_education_points():
    row = dict(data_parser.load_merged_users()[1])
    points = {}
    for label in ("High School", "Below high school", "None"):
        out = user_service.score({**row, "education_level": label, "education": None})
        points[label] = out["subfactor_breakdown"]["1.4_education_level"]["score"]
    assert points == {"High School": 20, "Below high school": 0, "None": 0}


def test_profile_numbers_have_sane_upper_bounds(client, login_as):
    login_as("USR_007")
    url = f"{API}/scoring/USR_007/profile"
    for body in (
        {"monthly_income": 1e12},
        {"months_at_job": 5000},
        {"dti": 99},
        {"risk_flags": 500},
    ):
        assert client.put(url, json=body).status_code == 422, body
    assert client.put(url, json={"monthly_income": 8000, "months_at_job": 40}).status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {"changes": {"months_at_job": "24"}},  # numeric field given text
        {"changes": {"on_time_rate": 5}},  # out of range
        {"changes": {"monthly_income": -1}},
        {"changes": {"housing": "banana"}},
        {"changes": {"education_level": "Astronaut"}},
        {"changes": {"education_level": 3}},
        {"changes": {"bogus": 1}},
        {"deltas": {"housing": 1}},  # text feature in deltas
        {"deltas": {"monthly_income": 1e12}},
        {"deltas": {"bogus": 1}},
    ],
)
def test_what_if_rejects_bad_edits(client, login_as, body):
    login_as("USR_002")
    assert _what_if(client, body).status_code == 422


def test_what_if_accepts_valid_edits_and_normalises_education(client, login_as):
    login_as("USR_002")
    ok = _what_if(client, {"changes": {"on_time_rate": 0.99, "housing": "owner"}})
    assert ok.status_code == 200 and ok.json()["delta"] > 0
    assert _what_if(client, {"changes": {"education_level": "phd"}}).status_code == 200
    assert _what_if(client, {"deltas": {"dti": -0.1}}).status_code == 200


def test_fractional_delinquency_flag_counts_as_delinquent(client, login_as):
    login_as("USR_002")  # clean history in the seed data
    r = _what_if(client, {"changes": {"delinq_90plus": 0.6}}).json()
    assert r["delta"] < 0
    assert any(c["key"] == "3.4_delinquency_severity" for c in r["factor_changes"])
    profile, _ = data_parser.normalise_profile({"delinq_30plus": 0.2, "delinq_60plus": 0})
    assert profile["delinq_30plus"] == 1 and profile["delinq_60plus"] == 0


def test_pdf_survives_markup_in_stored_values():
    """Old rows may hold free text from before validation; it must be printed, not parsed."""
    row = dict(data_parser.load_merged_users()[1])
    row["education_level"] = "<b>unclosed & <img src='file:///etc/hosts'> <font color="
    result = user_service.score(row)
    pdf = report_service.build_pdf(result, "USR_<x>&")
    assert pdf.startswith(b"%PDF")
