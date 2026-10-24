import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from services import data_parser


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=1, max_length=200)
    role: Literal["user", "lender"] = "user"


class LenderRegisterIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    username: str = Field(pattern=r"^[a-z0-9_]{3,40}$")
    password: str = Field(min_length=8, max_length=200)
    min_credit_score_requirement: float = Field(default=650, ge=0, le=1000)
    max_pd_threshold: float = Field(default=0.35, gt=0, le=1)


def _bounded(key: str, *, integer: bool = False):
    low, high = data_parser.INPUT_LIMITS[key]
    if integer:
        return Field(default=None, ge=int(low), le=int(high))
    return Field(default=None, ge=low, le=high, allow_inf_nan=False)


def _education(value: str | None) -> str | None:
    if value is None:
        return None
    label = data_parser.canonical_education(value)
    if label is None:
        raise ValueError(
            f"unknown education level; use one of {list(data_parser.EDUCATION_LEVELS)}"
        )
    return label


class ProfileIn(BaseModel):
    """Any subset of the engine's inputs; omitted fields keep their stored value."""

    model_config = ConfigDict(extra="forbid")
    age: int | None = Field(default=None, ge=18, le=100)
    education_level: str | None = Field(default=None, max_length=40)
    employment_status: Literal["Employed", "Self-Employed", "Student", "Unemployed"] | None = None
    city_tier: int | None = Field(default=None, ge=1, le=3)
    months_at_job: float | None = _bounded("months_at_job")
    housing: Literal["owner", "rent", "none"] | None = None
    rent_on_time_months: float | None = _bounded("rent_on_time_months")
    digital_payment_rate: float | None = _bounded("digital_payment_rate")
    monthly_income: float | None = _bounded("monthly_income")
    monthly_spend: float | None = _bounded("monthly_spend")
    essential_pct: float | None = _bounded("essential_pct")
    cashflow_volatility: float | None = _bounded("cashflow_volatility")
    savings_days: float | None = _bounded("savings_days")
    on_time_rate: float | None = _bounded("on_time_rate")
    dti: float | None = _bounded("dti")
    credit_util: float | None = _bounded("credit_util")
    delinq_30plus: Literal[0, 1] | None = None
    delinq_60plus: Literal[0, 1] | None = None
    delinq_90plus: Literal[0, 1] | None = None
    positive_habits: int | None = _bounded("positive_habits", integer=True)
    risk_flags: int | None = _bounded("risk_flags", integer=True)

    _canonical_education = field_validator("education_level")(_education)


class WhatIfIn(BaseModel):
    """Hypothetical edits. Every key and value is checked: the simulator re-scores them as-is."""

    changes: dict[str, float | str] = {}  # absolute new values, e.g. {"months_at_job": 24}
    deltas: dict[str, float] = {}  # relative edits, e.g. {"dti": 0.1} for extra debt

    @model_validator(mode="after")
    def _check_edits(self):
        for key, value in self.changes.items():
            if key == "housing":
                if value not in data_parser.HOUSING_VALUES:
                    raise ValueError(f"housing must be one of {list(data_parser.HOUSING_VALUES)}")
            elif key == "education_level":
                if not isinstance(value, str):
                    raise ValueError("education_level must be text")
                self.changes[key] = _education(value)
            elif key in data_parser.NUMERIC_KEYS:
                low, high = data_parser.INPUT_LIMITS[key]
                number_ok = isinstance(value, int | float) and not isinstance(value, bool)
                if not number_ok or not math.isfinite(value) or not low <= value <= high:
                    raise ValueError(f"{key} must be a number between {low} and {high}")
            else:
                raise ValueError(f"unknown feature: {key}")
        for key, value in self.deltas.items():
            if key not in data_parser.NUMERIC_KEYS:
                raise ValueError(f"unknown or non-numeric feature: {key}")
            low, high = data_parser.INPUT_LIMITS[key]
            if not math.isfinite(value) or abs(value) > high - low:
                raise ValueError(f"{key} change must be within +/-{high - low}")
        return self


class ApplyIn(BaseModel):
    product_id: str


class OfferResponseIn(BaseModel):
    decision: Literal["ACCEPTED", "DECLINED"]


class OfferPushIn(BaseModel):
    anon_lead_ids: list[str] = Field(min_length=1, max_length=500)
    loan_amount: float = Field(gt=0)
    interest_rate: float = Field(gt=0, le=100)
    offer_type: Literal["Loan", "Credit Card"] = "Loan"


class RegisterIn(ProfileIn):
    """New-user signup: account details plus the whole profile (every profile field is optional)."""

    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=160)
    password: str = Field(min_length=8, max_length=200)
    # Opt-in: until this is true the borrower does not appear in any lender's candidate search.
    share_with_lenders: bool = False


class ConsentIn(BaseModel):
    share_with_lenders: bool
