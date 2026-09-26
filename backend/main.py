from fastapi import FastAPI


# Import ORM models so that all tables
# are registered in Base.metadata.

from models.demographic import Demographic
from models.feature import Feature
from models.transaction import Transaction
from models.product import Product
from models.score import (
    CreditScore,
    ScoreFactor
)
from models.recommendation import (
    Recommendation
)


from db.database import (
    Base,
    engine
)


from backend.api.health import (
    router as health_router
)

from backend.api.users import (
    router as users_router
)

from backend.api.transactions import (
    router as transactions_router
)

from backend.api.scoring import (
    router as scoring_router
)

from backend.api.products import (
    router as products_router
)

from backend.api.recommendations import (
    router as recommendations_router
)

from backend.api.reports import (
    router as reports_router
)

from backend.api.whatif import (
    router as whatif_router
)


# Create SQLite tables
Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="AltCredit API",
    version="1.0.0"
)


app.include_router(
    health_router,
    prefix="/api"
)

app.include_router(
    users_router,
    prefix="/api"
)

app.include_router(
    transactions_router,
    prefix="/api"
)

app.include_router(
    scoring_router,
    prefix="/api"
)

app.include_router(
    products_router,
    prefix="/api"
)

app.include_router(
    recommendations_router,
    prefix="/api"
)

app.include_router(
    reports_router,
    prefix="/api"
)

app.include_router(
    whatif_router,
    prefix="/api"
)


@app.get("/")
def root():

    return {
        "application": "AltCredit",
        "status": "running"
    }