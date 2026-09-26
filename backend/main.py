from fastapi import FastAPI

from backend.db.database import Base, engine

from backend.api.health import router as health_router
from backend.api.users import router as users_router
from backend.api.transactions import router as transactions_router
from backend.api.scoring import router as scoring_router
from backend.api.products import router as products_router
from backend.api.recommendations import router as recommendations_router
from backend.api.reports import router as reports_router
from backend.api.whatif import router as whatif_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AltCredit API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(scoring_router)
app.include_router(products_router)
app.include_router(recommendations_router)
app.include_router(reports_router)
app.include_router(whatif_router)


@app.get("/")
def root():
    return {
        "application": "AltCredit",
        "status": "running"
    }