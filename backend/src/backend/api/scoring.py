from fastapi import APIRouter, HTTPException

from app.scoring.score_engine import calculate_score
from app.services.scoring_service import get_risk_category


router = APIRouter(
    prefix="/score",
    tags=["Scoring"]
)


@router.post("/calculate")
def calculate_credit_score(features: dict):

    try:

        result = calculate_score(features)

        result["risk_category"] = get_risk_category(
            result["final_score"]
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )