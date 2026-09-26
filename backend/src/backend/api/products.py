from fastapi import APIRouter

from ..database.database import get_connection
from ..schemas.product import ProductCreate


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("/")
def create_product(product: ProductCreate):

    connection = get_connection()

    connection.execute("""
        INSERT OR REPLACE INTO products (
            product_id,
            name,
            type,
            min_score_required,
            interest_rate
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        product.product_id,
        product.name,
        product.type,
        product.min_score_required,
        product.interest_rate
    ))

    connection.commit()
    connection.close()

    return {
        "message": "Product created",
        "product_id": product.product_id
    }


@router.get("/")
def get_products():

    connection = get_connection()

    rows = connection.execute(
        "SELECT * FROM products"
    ).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]