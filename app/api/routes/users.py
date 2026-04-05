"""
Модуль API пользователя.

Предоставляет эндпоинты для работы с текущим пользователем:
- Получение профиля текущего пользователя
- Обновление профиля текущего пользователя
- Мягкое удаление текущего пользователя

Все эндпоинты требуют:
- Аутентификации (Bearer token)

Rate limits:
- Получение профиля: 60 запросов в минуту
- Обновление профиля: 5 запросов в минуту
- Удаление профиля: 1 запрос в минуту
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models import User
from app.schemas.common import APIMessage
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(
    prefix='/users',
    tags=['users'],
    responses={
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        404: {
            "description": "Пользователь не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
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
# ЭНДПОИНТЫ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
# ============================================================================

@router.get('/me', response_model=UserResponse)
@limiter.limit("60 per minute")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение профиля текущего пользователя.

    Возвращает данные пользователя, извлечённого из access token.

    **Необходимые права:** Аутентифицированный пользователь

    **Возвращает:**
        UserResponse: Данные текущего пользователя

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **404**: Пользователь не найден
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        GET /api/v1/users/me
        Authorization: Bearer <access_token>

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
    return await UserService(session).get_current(current_user)


@router.patch('/me', response_model=UserResponse)
@limiter.limit("5 per minute")
async def update_me(
    request: Request,
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Обновление профиля текущего пользователя.

    Обновляет только переданные поля профиля текущего пользователя.

    **Необходимые права:** Аутентифицированный пользователь

    **Тело запроса:**
        Поля зависят от схемы UserUpdateRequest.
        Будут обновлены только переданные значения.

    **Возвращает:**
        UserResponse: Обновлённые данные пользователя

    **Возможные ошибки:**
        - **400**: Невалидные входные данные
        - **401**: Пользователь не авторизован
        - **404**: Пользователь не найден
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        PATCH /api/v1/users/me
        Authorization: Bearer <access_token>
        {
            "full_name": "John Updated"
        }

    **Пример ответа:**
        ```json
        {
            "id": 1,
            "full_name": "John Updated",
            "email": "john@example.com",
            "is_active": true
        }
        ```
    """
    return await UserService(session).update_me(current_user, payload)


@router.delete('/me', response_model=APIMessage)
@limiter.limit("1 per minute")
async def delete_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Мягкое удаление текущего пользователя.

    Выполняет soft delete профиля текущего пользователя
    и завершает его текущую сессию.

    **Необходимые права:** Аутентифицированный пользователь

    **Возвращает:**
        APIMessage: Сообщение об успешном удалении пользователя

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **404**: Пользователь не найден
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        DELETE /api/v1/users/me
        Authorization: Bearer <access_token>

    **Пример ответа:**
        ```json
        {
            "message": "User soft-deleted and logged out"
        }
        ```
    """
    await UserService(session).soft_delete_me(current_user)
    return APIMessage(message='User soft-deleted and logged out')
