from fastapi import (
    APIRouter,
    Depends,
    Query
)

from sqlalchemy.orm import Session

from db.database import get_db

from models.product import Product

from backend.services.recommendation_service import (
    recommend_products
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("")
def get_recommendations(
    score: float = Query(
        ...,
        ge=0,
        le=1000
    ),
    db: Session = Depends(get_db)
):

    products = (
        db.query(Product)
        .all()
    )

    return {

        "score": score,

        "recommendations":
            recommend_products(
                products,
                score
            )
    }