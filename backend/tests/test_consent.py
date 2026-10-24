import pytest
from sqlalchemy import select

from app import models
from core.config import settings
from core.database import SessionLocal
from services import seed

API = settings.api_prefix


def _register(client, email, **extra):
    r = client.post(
        f"{API}/auth/register",
        json={"full_name": "Consent Test", "email": email, "password": "longenough1", **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _lead_id(user_id):
    with SessionLocal() as db:
        return db.scalar(
            select(models.AnonymousLead.anon_lead_id)
            .join(models.LoanApplication)
            .where(models.LoanApplication.user_id == user_id)
        )


def _visible_to_lenders(client, lender_headers, lender_id, lead_id):
    r = client.get(
        f"{API}/lender/{lender_id}/candidates",
        params={"q": lead_id, "only_qualifying": False},
        headers=lender_headers,
    )
    return r.json()["total"] == 1


@pytest.fixture
def lender(client, headers_for):
    return "1", headers_for("primebank", "lender")


def test_new_registrants_are_hidden_until_they_opt_in(client, lender):
    lender_id, lh = lender
    reg = _register(client, "private.person@example.test")
    uh = {"Authorization": f"Bearer {reg['token']}"}
    uid, lead = reg["user_id"], _lead_id(reg["user_id"])
    assert not _visible_to_lenders(client, lh, lender_id, lead)
    assert client.get(f"{API}/users/{uid}/consent", headers=uh).json() == {
        "share_with_lenders": False
    }
    assert client.get(f"{API}/dashboard/{uid}", headers=uh).json()["share_with_lenders"] is False

    on = client.put(f"{API}/users/{uid}/consent", json={"share_with_lenders": True}, headers=uh)
    assert on.json() == {"share_with_lenders": True, "withdrawn_offers": 0}
    assert _visible_to_lenders(client, lh, lender_id, lead)


def test_signup_opt_in_puts_the_user_in_the_pool_and_stays_out_of_the_profile(client, lender):
    lender_id, lh = lender
    reg = _register(client, "open.person@example.test", share_with_lenders=True)
    assert _visible_to_lenders(client, lh, lender_id, _lead_id(reg["user_id"]))
    with SessionLocal() as db:
        app = db.scalar(
            select(models.LoanApplication).where(models.LoanApplication.user_id == reg["user_id"])
        )
        assert "share_with_lenders" not in app.profile


def test_rescoring_never_flips_the_consent_flag(client, lender):
    lender_id, lh = lender
    reg = _register(client, "rescore.person@example.test", share_with_lenders=True)
    uh = {"Authorization": f"Bearer {reg['token']}"}
    uid, lead = reg["user_id"], _lead_id(reg["user_id"])
    client.put(f"{API}/users/{uid}/consent", json={"share_with_lenders": False}, headers=uh)
    assert client.put(
        f"{API}/scoring/{uid}/profile", json={"months_at_job": 40}, headers=uh
    ).is_success
    assert not _visible_to_lenders(client, lh, lender_id, lead)  # still opted out
    client.put(f"{API}/users/{uid}/consent", json={"share_with_lenders": True}, headers=uh)
    assert client.put(
        f"{API}/scoring/{uid}/profile", json={"months_at_job": 41}, headers=uh
    ).is_success
    assert _visible_to_lenders(client, lh, lender_id, lead)


def test_opting_out_withdraws_open_offers_and_hides_the_candidate(client, headers_for):
    lh = headers_for("microfin", "lender")
    reg = _register(
        client,
        "withdraw.person@example.test",
        share_with_lenders=True,
        monthly_income=9000,
        on_time_rate=0.99,
        monthly_spend=2000,
        months_at_job=40,
        housing="owner",
        savings_days=200,
    )
    uid, lead = reg["user_id"], _lead_id(reg["user_id"])
    uh = {"Authorization": f"Bearer {reg['token']}"}
    pushed = client.post(
        f"{API}/lender/2/offers",
        json={"anon_lead_ids": [lead], "loan_amount": 500, "interest_rate": 8},
        headers=lh,
    ).json()
    assert len(pushed["created"]) == 1, pushed
    offer_id = pushed["created"][0]["offer_id"]
    assert client.get(f"{API}/dashboard/{uid}", headers=uh).json()["has_pending_offers"]

    off = client.put(f"{API}/users/{uid}/consent", json={"share_with_lenders": False}, headers=uh)
    assert off.json() == {"share_with_lenders": False, "withdrawn_offers": 1}
    offers = client.get(f"{API}/lender/2/offers", params={"status": "WITHDRAWN"}, headers=lh)
    assert [o["offer_id"] for o in offers.json()] == [offer_id]
    assert not client.get(f"{API}/dashboard/{uid}", headers=uh).json()["has_pending_offers"]
    assert client.get(f"{API}/lender/2/candidates/{lead}", headers=lh).status_code == 404
    again = client.post(
        f"{API}/lender/2/offers",
        json={"anon_lead_ids": [lead], "loan_amount": 500, "interest_rate": 8},
        headers=lh,
    ).json()
    assert again["created"] == [] and again["skipped"][0]["reason"] == "not found"
    late = client.post(
        f"{API}/products/{uid}/offers/{offer_id}/respond",
        json={"decision": "ACCEPTED"},
        headers=uh,
    )
    assert late.status_code == 409  # a withdrawn offer cannot be accepted (and so reveal identity)


def test_only_the_owner_can_change_consent(client, login_as):
    login_as("USR_002")
    r = client.put(f"{API}/users/USR_003/consent", json={"share_with_lenders": False})
    assert r.status_code == 403


def test_legacy_rows_without_a_consent_value_stay_in_the_pool():
    with SessionLocal() as db:
        db.get(models.User, "USR_020").share_with_lenders = None
        db.commit()
        seed._backfill_consent(db)
        assert db.get(models.User, "USR_020").share_with_lenders is True


def test_pd_is_labelled_as_score_derived_everywhere(client, login_as):
    login_as("USR_002")
    assert client.get(f"{API}/scoring/USR_002").json()["pd_basis"] == "score_derived"
    assert client.get(f"{API}/dashboard/USR_002").json()["score"]["pd_basis"] == "score_derived"
    assert client.get(f"{API}/scoring/USR_002/export.json").json()["pd_basis"] == "score_derived"
    login_as("primebank", "lender")
    top = client.get(f"{API}/lender/1/candidates", params={"limit": 1}).json()["results"][0]
    assert top["pd_basis"] == "score_derived"
