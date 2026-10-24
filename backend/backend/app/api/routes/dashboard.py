from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.api.dependencies import existing_user
from core.database import get_db
from services import report_service, user_service
from services.rule_engine import c as ml_config

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{user_id}")
def dashboard(user: models.User = Depends(existing_user), db: Session = Depends(get_db)):
    """Everything the user-mode dashboard needs in a single call."""
    result = user_service.score_user(db, user)
    expl = result["explanation"]
    recs = result["recommendations"]
    verdict, why = report_service.decision(result)
    pending = db.scalar(
        select(models.LoanOffer.offer_id)
        .join(models.AnonymousLead)
        .join(models.LoanApplication)
        .where(
            models.LoanApplication.user_id == user.user_id,
            models.LoanOffer.status == "OFFERED",
        )
        .limit(1)
    )
    return {
        "user_id": user.user_id,
        "score": {
            "value": result["credit_score"],
            "max": result["max_score"],
            "risk_tier": result["risk_tier"],
            "predicted_pd": result["predicted_pd"],
            "pd_basis": result["pd_basis"],
            "decision": verdict,
            "decision_reason": why,
        },
        "score_bands": [
            {"label": t["label"], "min_score": t["min_score"]}
            for t in reversed(ml_config.RISK_TIERS)
        ],
        "pillars": result["pillar_breakdown"],
        "credit_drivers": {
            "top_positive": expl["top_contributors"],
            "negative": expl["negative_factors"],
            "weak": expl["weak_factors"],
            "all_factors": expl["all_factors"],
        },
        "next_steps": {
            "eligible_products": recs["eligible_products"],
            "next_product": recs["next_product"],
            "improvement_suggestions": expl["improvement_suggestions"],
        },
        "history": user_service.score_history(db, user.user_id),
        "has_pending_offers": pending is not None,
        "share_with_lenders": bool(user.share_with_lenders),
        "data_completeness": result["data_completeness"],
        "missing_fields": result["missing_fields"],
    }
