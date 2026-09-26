from fastapi import APIRouter

from app.services.whatif_service import simulate_what_if


router = APIRouter(
    prefix="/what-if",
    tags=["What-If"]
)


@router.post("/simulate")
def simulate(payload: dict):

    current_features = payload["current_features"]

    changes = payload.get(
        "changes",
        {}
    )

    result = simulate_what_if(
        current_features,
        changes
    )

    return {
        "current_score": payload.get(
            "current_score"
        ),
        "simulated_score": result["final_score"],
        "score_change": (
            result["final_score"]
            -
            payload.get("current_score", 0)
        ),
        "details": result
    }