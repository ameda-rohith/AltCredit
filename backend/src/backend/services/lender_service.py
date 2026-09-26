from sqlalchemy.orm import Session

from models.score import CreditScore
from models.user import User


def search_candidates(
    db: Session,
    min_score: float = 0,
    max_score: float = 1000,
    limit: int = 50
):

    results = (
        db.query(
            CreditScore,
            User
        )
        .join(
            User,
            CreditScore.user_id == User.user_id
        )
        .filter(
            CreditScore.score >= min_score,
            CreditScore.score <= max_score
        )
        .order_by(
            CreditScore.score.desc()
        )
        .limit(limit)
        .all()
    )

    candidates = []

    for score, user in results:

        candidates.append({
            "user_id": user.user_id,
            "score": score.score,
            "risk_category": score.risk_category,

            # Do not expose real PII.
            "anonymized": True
        })

    return candidates


def get_candidate(
    db: Session,
    user_id: str
):

    score = (
        db.query(CreditScore)
        .filter(
            CreditScore.user_id == user_id
        )
        .order_by(
            CreditScore.created_at.desc()
        )
        .first()
    )

    if not score:
        return None

    return {
        "user_id": user_id,
        "score": score.score,
        "risk_category": score.risk_category,
        "anonymized": True
    }