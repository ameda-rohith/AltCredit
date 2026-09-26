from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    role = Column(
        String(30),
        default="user",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )