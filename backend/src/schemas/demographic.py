from pydantic import BaseModel


class DemographicCreate(BaseModel):
    user_id: str
    age: int
    employment_status: str
    education_level: str
    monthly_income: float
    city_tier: str

    employment_months: int = 0
    residency_months: int = 0

    housing_status: str = "unstable"