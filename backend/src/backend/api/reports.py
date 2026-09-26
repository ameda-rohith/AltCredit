from fastapi import APIRouter, HTTPException

from ..database.database import get_connection


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get("/{user_id}")
def get_transparency_report(user_id: str):

    connection = get_connection()

    score = connection.execute("""
        SELECT *
        FROM credit_scores
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    if not score:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Score not calculated"
        )

    factors = connection.execute("""
        SELECT
            factor_name,
            points,
            impact,
            reason
        FROM score_factors
        WHERE score_id = ?
    """, (score["id"],)).fetchall()

    connection.close()

    return {
        "user_id": user_id,
        "score": score["score"],
        "risk_category": score["risk_category"],
        "decision_basis": [
            dict(factor)
            for factor in factors
        ],
        "disclaimer": (
            "Prototype credit assessment output "
            "based on synthetic data."
        )
    }