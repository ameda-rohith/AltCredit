from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.api.dependencies import existing_lender
from app.models import _now
from core.config import settings
from core.database import get_db
from services import user_service
from services.rule_engine import c as ml_config

router = APIRouter(prefix="/lender/{lender_id}", tags=["lender"])


def _lead_view(lead: models.AnonymousLead) -> dict:
    """Anonymised candidate: no name, address, phone or user_id."""
    score = lead.credit_score
    tier = next((t["label"] for t in ml_config.RISK_TIERS if score >= t["min_score"]), "")
    return {
        "anon_lead_id": lead.anon_lead_id,
        "credit_score": score,
        "risk_tier": tier,
        "predicted_pd": lead.predicted_pd,
        "pd_basis": user_service.PD_BASIS,
        "monthly_income": lead.monthly_income,
        "debt_to_income": lead.debt_to_income,
    }


def _like_pattern(text: str) -> str:
    """`%text%` with LIKE wildcards in the user's text matched literally (escape char: \\)."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("")
def me(lender: models.Lender = Depends(existing_lender)):
    return {
        "lender_id": lender.lender_id,
        "company_name": lender.company_name,
        "min_credit_score_requirement": lender.min_credit_score_requirement,
        "max_pd_threshold": lender.max_pd_threshold,
    }


@router.get("/candidates")
def search_candidates(
    min_score: float | None = Query(None, ge=0, le=1000),
    max_score: float | None = Query(None, ge=0, le=1000),
    max_pd: float | None = Query(None, ge=0, le=1),
    min_income: float | None = Query(None, ge=0),
    max_dti: float | None = Query(None, ge=0),
    q: str | None = Query(None, max_length=40),
    only_qualifying: bool = True,
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|income_desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    lender: models.Lender = Depends(existing_lender),
    db: Session = Depends(get_db),
):
    """Search/filter candidates.

    `only_qualifying` (default) also applies the lender's own score/PD policy.
    """
    lead = models.AnonymousLead
    conds = [lead.is_active.is_(True)]
    if only_qualifying:
        conds += [
            lead.credit_score >= lender.min_credit_score_requirement,
            lead.predicted_pd <= lender.max_pd_threshold,
        ]
    if q and q.strip():
        conds.append(lead.anon_lead_id.ilike(_like_pattern(q.strip()), escape="\\"))
    if min_score is not None:
        conds.append(lead.credit_score >= min_score)
    if max_score is not None:
        conds.append(lead.credit_score <= max_score)
    if max_pd is not None:
        conds.append(lead.predicted_pd <= max_pd)
    if min_income is not None:
        conds.append(lead.monthly_income >= min_income)
    if max_dti is not None:
        conds.append(lead.debt_to_income <= max_dti)
    order = {
        "score_desc": lead.credit_score.desc(),
        "score_asc": lead.credit_score.asc(),
        "income_desc": lead.monthly_income.desc(),
    }[sort]
    total = db.scalar(select(func.count()).select_from(lead).where(*conds))
    rows = db.scalars(
        select(lead).where(*conds).order_by(order, lead.anon_lead_id).limit(limit).offset(offset)
    ).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [_lead_view(r) for r in rows],
    }


@router.get("/candidates/{anon_lead_id}")
def candidate_detail(
    anon_lead_id: str,
    lender: models.Lender = Depends(existing_lender),
    db: Session = Depends(get_db),
):
    """Risk profile of one candidate - factor breakdown without identity."""
    lead = db.get(models.AnonymousLead, anon_lead_id)
    if lead is None or not lead.is_active:
        raise HTTPException(404, "candidate not found")
    result = user_service.score({**lead.application.profile})
    return {
        **_lead_view(lead),
        "pillar_breakdown": result["pillar_breakdown"],
        "subfactors": result["subfactor_breakdown"],
        "top_factors": result["explanation"]["top_contributors"][:3],
        "qualifies": lead.credit_score >= lender.min_credit_score_requirement
        and lead.predicted_pd <= lender.max_pd_threshold,
    }


@router.post("/offers", status_code=201)
def push_offers(
    body: schemas.OfferPushIn,
    lender: models.Lender = Depends(existing_lender),
    db: Session = Depends(get_db),
):
    """Push an offer to one or many candidates; only leads meeting the lender's policy get it."""
    lead_ids = list(dict.fromkeys(body.anon_lead_ids))
    leads = {
        lead.anon_lead_id: lead
        for lead in db.scalars(
            select(models.AnonymousLead).where(models.AnonymousLead.anon_lead_id.in_(lead_ids))
        )
    }
    # this lender's most recent offer per candidate (offer ids ascend, so the last one wins)
    latest: dict[str, models.LoanOffer] = {}
    for offer in db.scalars(
        select(models.LoanOffer)
        .where(
            models.LoanOffer.lender_id == lender.lender_id,
            models.LoanOffer.anon_lead_id.in_(lead_ids),
        )
        .order_by(models.LoanOffer.offer_id)
    ):
        latest[offer.anon_lead_id] = offer
    cooldown_ends = _now() - timedelta(days=settings.reoffer_cooldown_days)

    created, skipped = [], []

    def skip(lead_id: str, reason: str) -> None:
        skipped.append({"anon_lead_id": lead_id, "reason": reason})

    for lead_id in lead_ids:
        lead, previous = leads.get(lead_id), latest.get(lead_id)
        if lead is None or not lead.is_active:
            skip(lead_id, "not found")
        elif (
            lead.credit_score < lender.min_credit_score_requirement
            or lead.predicted_pd > lender.max_pd_threshold
        ):
            skip(lead_id, "does not meet lender policy")
        elif previous and previous.status == "OFFERED":
            skip(lead_id, "open offer already exists")
        elif previous and previous.status == "ACCEPTED":
            skip(lead_id, "offer already accepted")
        elif (
            previous
            and previous.status == "DECLINED"
            and (previous.responded_at or previous.created_at) > cooldown_ends
        ):
            skip(lead_id, "declined recently")
        else:
            offer = models.LoanOffer(
                lender_id=lender.lender_id,
                anon_lead_id=lead_id,
                offer_type=body.offer_type,
                loan_amount=body.loan_amount,
                interest_rate=body.interest_rate,
            )
            db.add(offer)
            created.append(offer)
    db.commit()
    return {
        "created": [{"offer_id": o.offer_id, "anon_lead_id": o.anon_lead_id} for o in created],
        "skipped": skipped,
    }


@router.get("/offers")
def list_offers(
    status: str | None = Query(None, pattern="^(OFFERED|ACCEPTED|DECLINED|WITHDRAWN)$"),
    lender: models.Lender = Depends(existing_lender),
    db: Session = Depends(get_db),
):
    """The lender's offers. Identity is revealed only once the user has ACCEPTED."""
    q = (
        select(models.LoanOffer)
        .where(models.LoanOffer.lender_id == lender.lender_id)
        .options(
            selectinload(models.LoanOffer.lead)
            .selectinload(models.AnonymousLead.application)
            .selectinload(models.LoanApplication.user)
        )
        .order_by(models.LoanOffer.offer_id.desc())
    )
    if status:
        q = q.where(models.LoanOffer.status == status)
    out = []
    for o in db.scalars(q):
        row = {
            "offer_id": o.offer_id,
            "anon_lead_id": o.anon_lead_id,
            "offer_type": o.offer_type,
            "loan_amount": o.loan_amount,
            "interest_rate": o.interest_rate,
            "status": o.status,
            "created_at": o.created_at,
            "contact": None,
        }
        if o.status == "ACCEPTED":
            user = o.lead.application.user
            row["contact"] = {"full_name": user.full_name, "email": user.email}
        out.append(row)
    return out
