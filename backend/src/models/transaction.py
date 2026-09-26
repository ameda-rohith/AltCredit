from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from backend.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    transaction_id = Column(
        String(100),
        unique=True,
        nullable=False
    )

    user_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    date = Column(Date)
    amount = Column(Float, nullable=False)
    category = Column(String(100))
    type = Column(String(20))
    payment_status = Column(String(50))