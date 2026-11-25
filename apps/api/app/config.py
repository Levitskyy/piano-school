from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# В контейнере код лежит в /app/app; локально — в <repo>/apps/api/app.
# Default env_file ищется только локально, в контейнере переменные задаёт compose.
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    secret_key: str = "dev-secret-change-me"

    database_url: str = "postgresql+asyncpg://piano:piano@localhost:5432/piano_school"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    courses_enabled: bool = True

    frontend_url: str = "http://localhost:3000"
    session_cookie_name: str = "ps_session"
    session_ttl_days: int = 30
    password_reset_ttl_minutes: int = 60
    email_verification_ttl_minutes: int = 60 * 24
    lesson_cancellation_hours: int = 24

    email_provider: str = "console"
    email_from: str = ""
    email_from_name: str = "Levickaya Piano"
    unisender_api_key: str = ""
    unisender_api_url: str = "https://goapi.unisender.ru/ru/transactional/api/v1"
    resend_api_key: str = ""
    resend_api_url: str = "https://api.resend.com"

    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_api_url: str = "https://api.yookassa.ru/v3"
    yookassa_return_url: str = "http://localhost:3000"
    prodamus_form_url: str = "https://payform.ru/"
    prodamus_secret_key: str = ""
    prodamus_payment_method: str = "monetaworld"
    prodamus_currency: str = "rub"
    payment_reservation_minutes: int = 15

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_local(self) -> bool:
        return self.environment == "local"

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
