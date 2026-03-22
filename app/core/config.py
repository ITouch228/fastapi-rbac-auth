from functools import lru_cache
import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field("RBAC Auth Service", alias="APP_NAME")
    debug: bool = Field(True, alias="DEBUG")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    cors_origins_raw: str = Field("", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        """Парсинг CORS origins из строки в список"""
        if not self.cors_origins_raw:
            return []
        try:
            return json.loads(self.cors_origins_raw)
        except json.JSONDecodeError:
            return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    # Настройки для rate limiting
    rate_limit_default: str = Field(
        "1000 per hour;100 per minute", alias="RATE_LIMIT_DEFAULT")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(
        7, alias="REFRESH_TOKEN_EXPIRE_DAYS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
