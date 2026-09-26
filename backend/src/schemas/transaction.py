from sqlalchemy import Column, Integer, String, Float
from backend.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    product_id = Column(
        String(50),
        unique=True,
        nullable=False
    )

    name = Column(String(200), nullable=False)

    type = Column(String(100))

    min_score_required = Column(Float)

    interest_rate = Column(String(50))