"""
Модуль API аутентификации.

Предоставляет эндпоинты для:
- Регистрации пользователей
- Входа в систему
- Обновления access token
- Выхода из системы

Все эндпоинты используют:
- Валидацию входных данных через Pydantic-схемы
- Сессию базы данных
- Rate limiting для защиты от злоупотреблений

Rate limits:
- Регистрация: 3 запроса в час
- Вход в систему: 20 запросов в минуту
- Обновление токена: 30 запросов в час
- Выход из системы: 10 запросов в минуту
"""

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.schemas.common import APIMessage
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
    responses={
        400: {
            "description": "Некорректный запрос",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request data"}
                }
            }
        },
        401: {
            "description": "Ошибка аутентификации",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials"}
                }
            }
        },
        409: {
            "description": "Конфликт данных",
            "content": {
                "application/json": {
                    "example": {"detail": "User already exists"}
                }
            }
        },
        429: {
            "description": "Слишком много запросов",
            "content": {
                "application/json": {
                    "example": {"detail": "Too Many Requests"}
                }
            }
        }
    }
)


# ============================================================================
# ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ
# ============================================================================

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3 per hour")
async def register(
    request: Request,
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя.

    **Тело запроса:**
        - **full_name** (str): Полное имя пользователя
        - **email** (str): Уникальный email пользователя
        - **password** (str): Пароль пользователя

    **Возвращает:**
        UserResponse: Созданный пользователь без чувствительных данных

    **Возможные ошибки:**
        - **400**: Невалидные входные данные
        - **409**: Пользователь с таким email уже существует
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        POST /api/v1/auth/register
        {
            "full_name": "John Doe",
            "email": "john@example.com",
            "password": "StrongPass123!"
        }

    **Пример ответа:**
        ```json
        {
            "id": 1,
            "full_name": "John Doe",
            "email": "john@example.com",
            "is_active": true
        }
        ```
    """
    return await AuthService(session).register(payload)


@router.post('/login', response_model=TokenPairResponse)
@limiter.limit("20 per minute")
async def login(
    request: Request,
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    """
    Вход пользователя в систему.

    Проверяет email и пароль пользователя, после чего
    возвращает пару access и refresh токенов.

    **Тело запроса:**
        - **email** (str): Email пользователя
        - **password** (str): Пароль пользователя

    **Заголовки:**
        - **User-Agent** (str, опционально): Информация о клиенте

    **Возвращает:**
        TokenPairResponse: Access token и refresh token

    **Возможные ошибки:**
        - **400**: Невалидные входные данные
        - **401**: Неверный email или пароль
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        POST /api/v1/auth/login
        {
            "email": "john@example.com",
            "password": "StrongPass123!"
        }

    **Пример ответа:**
        ```json
        {
            "access_token": "access_token_value",
            "refresh_token": "refresh_token_value",
            "token_type": "bearer"
        }
        ```
    """
    return await AuthService(session).login(payload, user_agent=user_agent)


@router.post('/refresh', response_model=TokenPairResponse)
@limiter.limit("30 per hour")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Обновление пары токенов.

    Принимает refresh token и возвращает новую пару
    access и refresh токенов.

    **Тело запроса:**
        - **refresh_token** (str): Действующий refresh token

    **Возвращает:**
        TokenPairResponse: Новая пара access и refresh токенов

    **Возможные ошибки:**
        - **400**: Невалидный refresh token
        - **401**: Refresh token недействителен или истёк
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        POST /api/v1/auth/refresh
        {
            "refresh_token": "refresh_token_value"
        }

    **Пример ответа:**
        ```json
        {
            "access_token": "new_access_token_value",
            "refresh_token": "new_refresh_token_value",
            "token_type": "bearer"
        }
        ```
    """
    return await AuthService(session).refresh(payload.refresh_token)


@router.post('/logout', response_model=APIMessage)
@limiter.limit("10 per minute")
async def logout(
    request: Request,
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Выход пользователя из системы.

    Инвалидирует переданный refresh token, чтобы он
    больше не мог использоваться для обновления сессии.

    **Тело запроса:**
        - **refresh_token** (str): Refresh token для отзыва

    **Возвращает:**
        APIMessage: Сообщение об успешном выходе из системы

    **Возможные ошибки:**
        - **400**: Невалидный refresh token
        - **401**: Refresh token недействителен или уже отозван
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        POST /api/v1/auth/logout
        {
            "refresh_token": "refresh_token_value"
        }

    **Пример ответа:**
        ```json
        {
            "message": "Logged out successfully"
        }
        ```
    """
    await AuthService(session).logout(payload.refresh_token)
    return APIMessage(message='Logged out successfully')
