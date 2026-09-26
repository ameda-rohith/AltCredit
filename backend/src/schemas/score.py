from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):

    user_id: str

    features: dict


class FactorResult(BaseModel):

    points: float
    impact: str
    reason: str


class ScoreResponse(BaseModel):

    user_id: str | None = None

    final_score: int = Field(
        ge=0,
        le=1000
    )

    raw_score: float

    lifestyle_score: float

    spending_score: float

    repayment_score: float

    bonus_points: float

    penalty_points: float

    risk_category: str

    lifestyle_factors: dict

    spending_factors: dict

    repayment_factors: dict