from pydantic import BaseModel, Field


class ProductCreate(BaseModel):

    product_id: str = Field(
        min_length=1,
        max_length=50
    )

    name: str = Field(
        min_length=1,
        max_length=200
    )

    type: str = Field(
        min_length=1,
        max_length=100
    )

    min_score_required: float = Field(
        ge=0,
        le=1000
    )

    interest_rate: str | None = None


class ProductResponse(BaseModel):

    product_id: str
    name: str
    type: str
    min_score_required: float
    interest_rate: str | None = None

    class Config:
        from_attributes = True