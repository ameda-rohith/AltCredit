from pydantic import BaseModel, Field


class FeatureInput(BaseModel):

    employment_months: int = Field(
        default=0,
        ge=0
    )

    housing_status: str = "none"

    rent_payment_months: int = Field(
        default=0,
        ge=0
    )

    digital_payment_rate: float = Field(
        default=0.0,
        ge=0,
        le=1
    )

    education_level: str = ""

    monthly_income: float = Field(
        default=0,
        ge=0
    )

    monthly_spend: float = Field(
        default=0,
        ge=0
    )

    spend_income_ratio: float = Field(
        default=1.0,
        ge=0
    )

    essential_ratio: float = Field(
        default=0.0,
        ge=0,
        le=1
    )

    cashflow_volatility: float = Field(
        default=0.0,
        ge=0
    )

    savings_days: float = Field(
        default=0.0,
        ge=0
    )

    on_time_payment_rate: float = Field(
        default=0.0,
        ge=0,
        le=1
    )

    debt_to_income: float = Field(
        default=1.0,
        ge=0
    )

    credit_utilization: float = Field(
    default=0.0,
    ge=0,
    le=1
)

    has_credit_line: bool = False

    delinq_30plus: int = Field(
        default=0,
        ge=0
    )

    delinq_60plus: int = Field(
        default=0,
        ge=0
    )

    delinq_90plus: int = Field(
        default=0,
        ge=0
    )

    qualifying_habits: int = Field(
        default=0,
        ge=0
    )

    risk_flags: int = Field(
        default=0,
        ge=0
    )