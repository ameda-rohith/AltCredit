from pydantic import BaseModel


class RecommendationResponse(BaseModel):

    product_id: str

    name: str

    type: str

    interest_rate: str | None = None

    min_score_required: float

    reason: str


class RecommendationListResponse(BaseModel):

    score: float

    recommendations: list[
        RecommendationResponse
    ]