from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    role = Column(
        String,
        default="user",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )