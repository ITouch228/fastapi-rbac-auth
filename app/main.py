"""
Главный модуль приложения.

Содержит:
- Создание экземпляра FastAPI приложения
- Настройку rate limiter
- Настройку CORS
- Подключение API роутеров
- Служебные эндпоинты проверки состояния приложения

Используется как точка входа для запуска
RBAC Auth Service.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, mock_resources, users
from app.core.config import get_settings
from app.core.rate_limiter import limiter, setup_rate_limiter

logger = logging.getLogger(__name__)

settings = get_settings()

settings.validate_cors_origins()

if not settings.debug and len(settings.jwt_secret_key) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must be at least 32 characters in production mode. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0",
    description=(
        "Custom authentication and RBAC authorization service "
        "with JWT and mock business resources."
    ),
)


# =========================================================================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# =========================================================================

setup_rate_limiter(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    max_age=600,
)


# =========================================================================
# ПОДКЛЮЧЕНИЕ API РОУТЕРОВ
# =========================================================================

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(mock_resources.router, prefix=settings.api_v1_prefix)


# =========================================================================
# СЛУЖЕБНЫЕ ЭНДПОИНТЫ
# =========================================================================

@app.get("/health", tags=["Health"])
@limiter.limit("10/minute")
async def health(request: Request):
    """
    Проверка состояния приложения.

    Используется для healthcheck и мониторинга
    доступности сервиса.

    **Возвращает:**
        dict: Статус работоспособности приложения

    **Пример ответа:**
        ```json
        {
            "status": "ok"
        }
        ```
    """
    return {"status": "ok"}


@app.get('/')
@limiter.limit("5/minute")
async def root(request: Request):
    """
    Корневой эндпоинт приложения.

    Возвращает базовое сообщение о том,
    что сервис запущен и доступен.

    **Возвращает:**
        dict: Информационное сообщение о сервисе

    **Пример ответа:**
        ```json
        {
            "message": "RBAC Auth Service is running"
        }
        ```
    """
    return {'message': 'RBAC Auth Service is running'}
