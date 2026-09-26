from pydantic import BaseModel, Field


class WhatIfChanges(BaseModel):

    additional_savings: float = Field(
        default=0,
        ge=0
    )

    additional_monthly_spending: float = Field(
        default=0,
        ge=0
    )

    payment_rate_change: float = Field(
        default=0,
        ge=-1,
        le=1
    )

    additional_debt: float = Field(
        default=0,
        ge=0
    )

    cashflow_volatility_change: float = Field(
        default=0,
        ge=-1,
        le=1
    )

    additional_rent_payment_months: int = Field(
        default=0,
        ge=0
    )

    delinq_30plus_change: int = Field(
        default=0,
        ge=0
    )

    delinq_60plus_change: int = Field(
        default=0,
        ge=0
    )

    delinq_90plus_change: int = Field(
        default=0,
        ge=0
    )


class WhatIfRequest(BaseModel):

    user_id: str

    current_features: dict

    current_score: int | None = None

    changes: WhatIfChanges = WhatIfChanges()


class WhatIfResponse(BaseModel):

    current_score: int

    simulated_score: int

    score_change: int

    details: dict