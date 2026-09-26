from sqlalchemy import Column, Integer, String, Float
from backend.db.database import Base


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    employment_months = Column(Integer)
    digital_payment_rate = Column(Float)

    spend_income_ratio = Column(Float)
    essential_ratio = Column(Float)
    cashflow_volatility = Column(Float)
    savings_days = Column(Float)

    on_time_payment_rate = Column(Float)
    debt_to_income = Column(Float)
    credit_utilization = Column(Float)

    days_late = Column(Integer, default=0)
    multiple_misses = Column(Integer, default=0)

    qualifying_habits = Column(Integer, default=0)
    risk_flags = Column(Integer, default=0)