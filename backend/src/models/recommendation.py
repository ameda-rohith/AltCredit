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


class Recommendation(Base):

    __tablename__ = "recommendations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    product_id = Column(
        String(50),
        nullable=False
    )

    product_name = Column(
        String(200),
        nullable=False
    )

    product_type = Column(
        String(100),
        nullable=True
    )

    user_score = Column(
        Float,
        nullable=False
    )

    min_score_required = Column(
        Float,
        nullable=True
    )

    interest_rate = Column(
        String(50),
        nullable=True
    )

    reason = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )