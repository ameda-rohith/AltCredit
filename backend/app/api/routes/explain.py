from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.api.dependencies import existing_user
from core.config import settings
from core.database import get_db
from services import llm_explainer, user_service
from services.rate_limit import SlidingWindowLimiter

router = APIRouter(prefix="/scoring", tags=["explainability"])

# The LLM is a paid, slow upstream: cap fresh generations per user and reuse results while the
# score inputs are unchanged (cache hits are free and do not use up the budget).
explain_limiter = SlidingWindowLimiter(settings.explain_max_per_hour, 3600)
explain_cache = llm_explainer.ExplanationCache(settings.explain_cache_ttl_seconds)


@router.get("/{user_id}/explain")
def explain(user: models.User = Depends(existing_user), db: Session = Depends(get_db)):
    """LLM-written plain-language explanation of the user's current score."""
    scored = user_service.score_user(db, user)
    key = explain_cache.key(user.user_id, scored)
    narrative = explain_cache.get(key)
    if narrative is None:
        try:
            llm_explainer.ensure_configured()  # an unusable setup must not spend the user's budget
        except llm_explainer.LLMUnavailable as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
        if not explain_limiter.allow(user.user_id):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "explanation limit reached, try again later",
                headers={"Retry-After": str(explain_limiter.retry_after(user.user_id))},
            )
        try:
            narrative = llm_explainer.explain_score(scored)
        except llm_explainer.LLMUnavailable as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
        explain_cache.set(key, narrative)
    return {"user_id": user.user_id, "credit_score": scored["credit_score"], **narrative}
