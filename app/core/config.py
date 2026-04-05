"""
Модуль конфигурации приложения.

Содержит:
- Настройки приложения
- Настройки CORS
- Настройки базы данных и Redis
- Настройки rate limiting
- Настройки JWT аутентификации

Используется для:
- Загрузки конфигурации из переменных окружения
- Централизованного доступа к настройкам приложения
- Кэширования объекта настроек
"""

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс настроек приложения"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # =========================================================================
    # ОБЩИЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ
    # =========================================================================

    app_name: str = Field("RBAC Auth Service", alias="APP_NAME")
    debug: bool = Field(False, alias="DEBUG")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    # =========================================================================
    # НАСТРОЙКИ CORS
    # =========================================================================

    cors_origins_raw: str = Field("", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        """
        Преобразование CORS origins из строки в список.

        Поддерживает два формата:
        - JSON-массив
        - Строка, разделённая запятыми

        **Возвращает:**
            list[str]: Список разрешённых CORS origins
        """
        if not self.cors_origins_raw:
            return []

        try:
            return json.loads(self.cors_origins_raw)
        except json.JSONDecodeError:
            return [
                origin.strip()
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]

    # =========================================================================
    # НАСТРОЙКИ ИНФРАСТРУКТУРЫ
    # =========================================================================

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    # =========================================================================
    # НАСТРОЙКИ RATE LIMITING
    # =========================================================================

    rate_limit_default: str = Field(
        "1000 per hour;100 per minute",
        alias="RATE_LIMIT_DEFAULT"
    )

    # =========================================================================
    # НАСТРОЙКИ JWT
    # =========================================================================

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    access_token_expire_minutes: int = Field(
        15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Получение настроек приложения.

    Использует кэширование, чтобы объект настроек
    создавался только один раз за время работы приложения.

    **Возвращает:**
        Settings: Объект настроек приложения
    """
    return Settings()
