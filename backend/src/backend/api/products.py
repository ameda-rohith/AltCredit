from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from db.database import get_db

from models.product import Product

from schemas.product import (
    ProductCreate,
    ProductResponse
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(Product)
        .filter(
            Product.product_id
            == product.product_id
        )
        .first()
    )

    if existing:

        existing.name = product.name
        existing.type = product.type
        existing.min_score_required = (
            product.min_score_required
        )
        existing.interest_rate = (
            product.interest_rate
        )

    else:

        existing = Product(
            **product.model_dump()
        )

        db.add(existing)

    db.commit()

    db.refresh(existing)

    return existing


@router.get(
    "/",
    response_model=list[
        ProductResponse
    ]
)
def get_products(
    db: Session = Depends(get_db)
):

    return (
        db.query(Product)
        .all()
    )