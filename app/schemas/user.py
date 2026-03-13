"""
Модели Pydantic для работы с пользователями:
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.common import ORMBase

# ============================================================================
# Схемы для ответов
# ============================================================================


class UserResponse(ORMBase):
    """Схема ответа с данными пользователя"""

    id: int
    full_name: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "full_name": "Ivan Ivanov",
                "email": "ivan@example.com",
                "is_active": True,
            }
        },
    )


# ============================================================================
# Схемы для запросов
# ============================================================================

class UserUpdateRequest(BaseModel):
    """Схема запроса на обновление данных пользователя"""

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Ivan Petrov",
                "email": "ivan.petrov@example.com",
            }
        }
    )
