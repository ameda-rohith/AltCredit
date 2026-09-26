from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from db.database import Base


class CreditScore(Base):
    __tablename__ = "credit_scores"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    score = Column(Float, nullable=False)

    lifestyle_score = Column(Float)
    spending_score = Column(Float)
    repayment_score = Column(Float)

    bonus_points = Column(Float, default=0)
    penalty_points = Column(Float, default=0)

    risk_category = Column(String(50))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class ScoreFactor(Base):
    __tablename__ = "score_factors"

    id = Column(Integer, primary_key=True)

    score_id = Column(
        Integer,
        ForeignKey("credit_scores.id"),
        nullable=False
    )

    factor_name = Column(String(100))
    points = Column(Float)
    impact = Column(String(20))
    reason = Column(String(500))