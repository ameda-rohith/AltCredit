from sqlalchemy import (
    Column,
    Integer,
    String,
    Float
)

from db.database import Base


class Demographic(Base):

    __tablename__ = "demographics"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    age = Column(
        Integer,
        nullable=True
    )

    employment_status = Column(
        String(100),
        nullable=True
    )

    education_level = Column(
        String(100),
        nullable=True
    )

    monthly_income = Column(
        Float,
        nullable=True
    )

    city_tier = Column(
        String(50),
        nullable=True
    )

    months_at_job = Column(
        Integer,
        nullable=True
    )

    months_at_residence = Column(
        Integer,
        nullable=True
    )

    lifestyle_data = Column(
        String,
        nullable=True
    )