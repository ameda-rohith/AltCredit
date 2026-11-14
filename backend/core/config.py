"""Backend settings. Every value can be overridden through environment / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DEV_SECRET_KEY = "dev-only-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "AltCredit API"
    api_prefix: str = "/api/v1"

    @field_validator("secret_key", mode="before")
    @classmethod
    def _blank_secret_means_default(cls, value):
        """`SECRET_KEY=` (as in .env.example) must not become an empty signing key."""
        return value if str(value or "").strip() else DEV_SECRET_KEY

    @field_validator("data_dir", mode="before")
    @classmethod
    def _resolve_data_dir(cls, value):
        if value:
            p = Path(value)
            if p.exists():
                return p
        default_p = REPO_ROOT / "machine_learning" / "data"
        if default_p.exists():
            return default_p
        fallback_p = BACKEND_DIR / "data"
        if fallback_p.exists():
            return fallback_p
        return default_p

    @field_validator("merged_data_path", mode="before")
    @classmethod
    def _resolve_merged_data_path(cls, value):
        if value:
            p = Path(value)
            if p.exists():
                return p
        default_p = BACKEND_DIR / "data" / "merged_data.json"
        if default_p.exists():
            return default_p
        alt_p = REPO_ROOT / "backend" / "data" / "merged_data.json"
        if alt_p.exists():
            return alt_p
        return default_p

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value == "*":
                return ["*"]
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [o.strip() for o in value.split(",") if o.strip()]
        return value

    # --- Data ----------------------------------------------------------------
    # product catalog, transactions and ground-truth CSVs are read from machine_learning/data
    data_dir: Path = REPO_ROOT / "machine_learning" / "data"
    # user features live with the backend
    merged_data_path: Path = BACKEND_DIR / "data" / "merged_data.json"

    # --- Embedded database ------------------------------------------------
    database_url: str = f"sqlite:///{BACKEND_DIR / 'altcredit.db'}"
    seed_on_startup: bool = True

    # --- Auth (password checked against the database, then a signed bearer token) ---
    pbkdf2_iterations: int = 600_000
    # HMAC key for access tokens. The default is for local development only: set SECRET_KEY
    # in .env for anything shared, otherwise anyone can mint tokens.
    secret_key: str = DEV_SECRET_KEY
    token_ttl_minutes: int = 480
    # failed logins allowed per (username, client ip) inside the window
    login_max_failures: int = 10
    login_window_seconds: int = 300
    # Password given to seeded synthetic users / lenders. Dev-only default,
    # override in .env for anything shared.
    demo_password: str = "altcredit-demo"

    # A lender cannot re-offer to a candidate who declined its offer within this many days.
    reoffer_cooldown_days: int = 30

    # --- Bank integration (separate application, see bank_mock/) ------------
    bank_api_url: str = "http://127.0.0.1:8001"
    bank_api_key: str = "dev-only-bank-key"
    bank_timeout_seconds: float = 5.0

    # --- LLM explainer (Ollama Cloud); env names are OLLAMA_API_KEY, OLLAMA_MODEL, ... --------
    ollama_api_key: str = ""
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = "gpt-oss:120b"
    ollama_timeout_seconds: float = 30.0
    # Paid calls: at most this many fresh generations per user per hour; an unchanged score
    # is answered from a cache instead (and does not count).
    explain_max_per_hour: int = 5
    explain_cache_ttl_seconds: int = 3600

    # --- CORS: frontend origins allowed to call the API directly ------------
    cors_origins: list[str] | str = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
