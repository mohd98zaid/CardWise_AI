import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./cardwise.db")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    export_expiry_hours: int = int(os.getenv("EXPORT_EXPIRY_HOURS", "24"))
    enable_assistant: bool = os.getenv("ENABLE_ASSISTANT", "false").lower() == "true"


settings = Settings()
