from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
import redis.asyncio as aioredis
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Получаем настройки
settings = get_settings()

try:
    # Создаем Redis клиент
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf8",
        decode_responses=True
    )

    # Создаем лимитер с использованием Redis
    limiter = Limiter(
        key_func=get_remote_address,  # Используем IP-адрес как ключ
        storage_uri=settings.redis_url,  # URL Redis для хранения счетчиков
        # Используем настройку из конфига
        default_limits=[settings.rate_limit_default]
    )
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}. Using in-memory storage.")
    # Создаем лимитер с in-memory хранилищем в случае ошибки подключения к Redis
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default]
    )


def setup_rate_limiter(app: FastAPI):
    """
    Настройка rate limiter для приложения
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
