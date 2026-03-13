"""
Модуль настройки rate limiter.

Содержит:
- Создание Redis клиента для хранения счётчиков
- Создание Limiter для ограничения запросов
- Настройку обработчика ошибок rate limit

Используется для:
- Защиты API от злоупотреблений
- Ограничения частоты запросов
- Подключения Redis как backend для счётчиков лимитов

Если Redis недоступен:
- В debug режиме: используется in-memory storage
- В production режиме: выбрасывается ошибка (без fallback)
"""

import logging

import redis.asyncio as aioredis
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


# =========================================================================
# СОЗДАНИЕ REDIS КЛИЕНТА И RATE LIMITER
# =========================================================================

redis_client = None

try:
    # Создаём Redis клиент
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf8",
        decode_responses=True
    )

    # Создаём limiter с Redis-хранилищем
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.redis_url,
        default_limits=[settings.rate_limit_default]
    )
except Exception as e:
    if not settings.debug:
        logger.critical(
            "Redis unavailable in production mode. "
            "Rate limiting requires Redis for distributed sync. "
            "Error: %s", e
        )
        raise RuntimeError(
            "Redis is required for rate limiting in production mode. "
            f"Connection failed: {e}"
        ) from e

    logger.warning(
        "Failed to connect to Redis: %s. Using in-memory fallback (debug mode only).", e
    )

    # In-memory storage только для debug режима
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default],
        storage_uri="memory://",
    )


# =========================================================================
# НАСТРОЙКА RATE LIMITER
# =========================================================================

def setup_rate_limiter(app: FastAPI):
    """
    Настройка rate limiter для приложения.

    Добавляет limiter в состояние приложения
    и регистрирует обработчик ошибок превышения лимита.

    **Параметры:**
        - **app** (FastAPI): Экземпляр приложения FastAPI
    """
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler
    )
