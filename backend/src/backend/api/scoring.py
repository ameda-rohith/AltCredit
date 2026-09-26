from fastapi import (
    APIRouter,
    HTTPException
)

from schemas.score import ScoreRequest

from scoring.scoring_engine import (
    calculate_score
)

from backend.services.feature_service import (
    build_features
)

from backend.services.scoring_service import (
    get_risk_category
)


router = APIRouter(
    prefix="/score",
    tags=["Scoring"]
)


@router.post("/calculate")
def calculate_credit_score(
    payload: ScoreRequest
):

    try:

        features = build_features(
            payload.features
        )

        result = calculate_score(
            features
        )

        result["user_id"] = (
            payload.user_id
        )

        result["risk_category"] = (
            get_risk_category(
                result["final_score"]
            )
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc