from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field("RBAC Auth Service", alias="APP_NAME")
    debug: bool = Field(True, alias="DEBUG")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(..., alias="DATABASE_URL")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(
        7, alias="REFRESH_TOKEN_EXPIRE_DAYS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
