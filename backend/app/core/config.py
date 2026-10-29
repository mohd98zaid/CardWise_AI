import logging
import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when critical configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./cardwise.db")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    export_expiry_hours: int = int(os.getenv("EXPORT_EXPIRY_HOURS", "24"))
    enable_assistant: bool = os.getenv("ENABLE_ASSISTANT", "false").lower() == "true"
    auth_rate_limit: int = int(os.getenv("AUTH_RATE_LIMIT", "10"))
    trusted_proxies: tuple[str, ...] = tuple(
        p.strip() for p in os.getenv("TRUSTED_PROXIES", "").split(",") if p.strip()
    )
    initial_admin_email: str | None = os.getenv("INITIAL_ADMIN_EMAIL")
    initial_admin_password: str | None = os.getenv("INITIAL_ADMIN_PASSWORD")
    ai_provider: str = os.getenv("AI_PROVIDER", "disabled")
    ai_model: str = os.getenv("AI_MODEL", "")

    def validate(self) -> None:
        """Validate critical configuration constraints at startup."""
        if self.session_ttl_hours <= 0:
            raise ConfigurationError("SESSION_TTL_HOURS must be positive.")
        if self.export_expiry_hours <= 0:
            raise ConfigurationError("EXPORT_EXPIRY_HOURS must be positive.")
        if self.app_env == "production":
            if self.database_url.startswith("sqlite"):
                raise ConfigurationError(
                    "SQLite cannot be used as the production DATABASE_URL. "
                    "Use PostgreSQL or another production database."
                )
            if self.auth_rate_limit <= 0:
                raise ConfigurationError(
                    "AUTH_RATE_LIMIT cannot be disabled or zero in production."
                )
            logging.getLogger("cardwise.config").info(
                "Production configuration validated successfully."
            )


settings = Settings()
settings.validate()
