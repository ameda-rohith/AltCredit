from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Float,
    String
)

from db.database import Base


class Feature(Base):

    __tablename__ = "features"

    id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    employment_months = Column(
        Integer,
        default=0
    )

    housing_status = Column(
        String(50),
        default="none"
    )

    rent_payment_months = Column(
        Integer,
        default=0
    )

    digital_payment_rate = Column(
        Float,
        default=0.0
    )

    education_level = Column(
        String(100),
        default=""
    )

    monthly_income = Column(
        Float,
        default=0.0
    )

    monthly_spend = Column(
        Float,
        default=0.0
    )

    spend_income_ratio = Column(
        Float,
        default=1.0
    )

    essential_ratio = Column(
        Float,
        default=0.0
    )

    cashflow_volatility = Column(
        Float,
        default=0.0
    )

    savings_days = Column(
        Float,
        default=0.0
    )

    on_time_payment_rate = Column(
        Float,
        default=0.0
    )

    debt_to_income = Column(
        Float,
        default=1.0
    )

    credit_utilization = Column(
        Float,
        default=0.0
    )

    has_credit_line = Column(
        Boolean,
        default=False
    )

    delinq_30plus = Column(
        Integer,
        default=0
    )

    delinq_60plus = Column(
        Integer,
        default=0
    )

    delinq_90plus = Column(
        Integer,
        default=0
    )

    qualifying_habits = Column(
        Integer,
        default=0
    )

    risk_flags = Column(
        Integer,
        default=0
    )