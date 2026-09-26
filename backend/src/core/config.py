from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "AltCredit API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./altcredit.db"

    API_PREFIX: str = "/api"

    SCORE_MIN: int = 0
    SCORE_MAX: int = 1000

    # The rule-table maximum is 1270.
    # The use case defines the unified score as 0–1000.
    RAW_SCORE_MAX: int = 1270

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()