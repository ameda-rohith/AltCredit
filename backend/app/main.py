import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, consent, dashboard, explain, lender, products, scoring
from core.config import DEV_SECRET_KEY, settings
from core.database import SessionLocal, init_db
from services import seed

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.secret_key == DEV_SECRET_KEY:
        log.warning(
            "SECRET_KEY is the built-in dev default: set it in .env before sharing this API"
        )
    init_db()
    if settings.seed_on_startup:
        with SessionLocal() as db:
            seed.seed(db)
    yield


app = FastAPI(title=settings.app_name, version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


for r in (
    auth.router,
    scoring.router,
    explain.router,
    dashboard.router,
    consent.router,
    products.router,
    lender.router,
):
    app.include_router(r, prefix=settings.api_prefix)
