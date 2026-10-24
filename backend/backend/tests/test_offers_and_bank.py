from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.models import _now
from bank_mock.main import app as bank_app
from core.config import settings
from core.database import SessionLocal
from services import bank_client

API = settings.api_prefix


def _lead(user_id):
    with SessionLocal() as db:
        return db.scalar(
            select(models.AnonymousLead.anon_lead_id)
            .join(models.LoanApplication)
            .where(models.LoanApplication.user_id == user_id)
        )


def _qualifying_user(skip: int = 0, min_score: int = 760):
    """(user_id, lead_id) of a seeded candidate that every demo lender's policy accepts."""
    with SessionLocal() as db:
        row = db.execute(
            select(models.LoanApplication.user_id, models.AnonymousLead.anon_lead_id)
            .join(models.AnonymousLead)
            .where(
                models.AnonymousLead.credit_score >= min_score,
                models.AnonymousLead.is_active,
                models.LoanApplication.user_id <= "USR_500",  # seeded demo users share the password
            )
            .order_by(models.LoanApplication.user_id.desc())
            .offset(skip)
        ).first()
    return row.user_id, row.anon_lead_id


def _push(client, lender, lead_id):
    body = {"anon_lead_ids": [lead_id], "loan_amount": 1000, "interest_rate": 9}
    return client.post(f"{API}/lender/{lender}/offers", json=body).json()


def _set_offer(offer_id, **fields):
    with SessionLocal() as db:
        offer = db.get(models.LoanOffer, offer_id)
        for key, value in fields.items():
            setattr(offer, key, value)
        db.commit()


def test_declined_candidates_are_not_re_offered_until_the_cooldown_passes(client, login_as):
    user, lead = _qualifying_user(skip=0)
    lender = login_as("primebank", "lender")
    created = _push(client, lender, lead)["created"]
    assert len(created) == 1
    offer_id = created[0]["offer_id"]
    login_as(user)
    declined = client.post(
        f"{API}/products/{user}/offers/{offer_id}/respond", json={"decision": "DECLINED"}
    )
    assert declined.status_code == 200
    login_as("primebank", "lender")
    assert _push(client, lender, lead)["skipped"][0]["reason"] == "declined recently"
    # once the decline is older than the cooldown a new offer is fine
    _set_offer(offer_id, responded_at=_now() - timedelta(days=settings.reoffer_cooldown_days + 1))
    assert len(_push(client, lender, lead)["created"]) == 1


def test_accepted_offers_block_a_second_offer(client, login_as):
    lender = login_as("microfin", "lender")
    _, lead = _qualifying_user(skip=1)
    created = _push(client, lender, lead)["created"]
    assert created
    _set_offer(created[0]["offer_id"], status="ACCEPTED")
    assert _push(client, lender, lead)["skipped"][0]["reason"] == "offer already accepted"


def test_candidate_search_treats_like_wildcards_literally(client, login_as):
    lender = login_as("primebank", "lender")
    url = f"{API}/lender/{lender}/candidates"
    assert client.get(url, params={"q": "ANON-", "only_qualifying": False}).json()["total"] > 0
    for wildcard in ("%", "_", "\\"):
        found = client.get(url, params={"q": wildcard, "only_qualifying": False}).json()
        assert found["total"] == 0, wildcard


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"<html>oops</html>"),  # not JSON
        httpx.Response(200, json=["a", "list"]),
        httpx.Response(200, json={"no": "status"}),
        httpx.Response(200, json={"status": "MAYBE"}),
    ],
)
def test_unusable_bank_responses_become_502_not_500(client, login_as, monkeypatch, response):
    login_as("USR_014")
    monkeypatch.setattr(
        bank_client,
        "get_client",
        lambda: httpx.Client(
            base_url="http://bank", transport=httpx.MockTransport(lambda req: response)
        ),
    )
    r = client.post(f"{API}/products/USR_014/apply", json={"product_id": "P_01"})
    assert r.status_code == 502


def test_mock_bank_validates_its_input():
    payload = {
        "applicant_id": "a",
        "product_id": "P_01",
        "product_type": "Mortgage",
        "credit_score": 700,
        "min_score_required": 500,
        "monthly_income": 1000,
    }
    bank = TestClient(bank_app)
    headers = {"X-API-Key": settings.bank_api_key}
    assert bank.post("/v1/preapproved-offers", json=payload, headers=headers).status_code == 422
    payload |= {"product_type": "Loan", "min_score_required": 5000}
    assert bank.post("/v1/preapproved-offers", json=payload, headers=headers).status_code == 422
