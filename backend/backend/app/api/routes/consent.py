from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.dependencies import existing_user
from app.models import _now
from core.database import get_db

router = APIRouter(prefix="/users/{user_id}/consent", tags=["consent"])


@router.get("")
def get_consent(user: models.User = Depends(existing_user)):
    return {"share_with_lenders": bool(user.share_with_lenders)}


@router.put("")
def set_consent(
    body: schemas.ConsentIn,
    user: models.User = Depends(existing_user),
    db: Session = Depends(get_db),
):
    """Opt in to / out of lenders' anonymised candidate search.

    Opting out hides the candidate immediately and withdraws every offer still waiting for an
    answer; offers already ACCEPTED or DECLINED are history and stay as they are.
    """
    user.share_with_lenders = body.share_with_lenders
    lead_ids = db.scalars(
        select(models.AnonymousLead.anon_lead_id)
        .join(models.LoanApplication)
        .where(models.LoanApplication.user_id == user.user_id)
    ).all()
    withdrawn = 0
    if lead_ids:
        db.execute(
            update(models.AnonymousLead)
            .where(models.AnonymousLead.anon_lead_id.in_(lead_ids))
            .values(is_active=body.share_with_lenders)
        )
        if not body.share_with_lenders:
            withdrawn = db.execute(
                update(models.LoanOffer)
                .where(
                    models.LoanOffer.anon_lead_id.in_(lead_ids),
                    models.LoanOffer.status == "OFFERED",
                )
                .values(status="WITHDRAWN", responded_at=_now())
            ).rowcount
    db.commit()
    return {"share_with_lenders": body.share_with_lenders, "withdrawn_offers": withdrawn}
