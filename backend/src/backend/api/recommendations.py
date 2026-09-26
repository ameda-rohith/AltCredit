from fastapi import APIRouter, Query

from app.database.database import SessionLocal
from app.models.product import Product
from app.services.recommendation_service import recommend_products


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("")
def get_recommendations(
    score: float = Query(..., ge=0, le=1000)
):

    db = SessionLocal()

    try:

        products = db.query(Product).all()

        return {
            "score": score,
            "recommendations": recommend_products(
                products,
                score
            )
        }

    finally:

        db.close()