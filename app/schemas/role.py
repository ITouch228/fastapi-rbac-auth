"""
Модели Pydantic для работы с ролями:
"""

import re
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import ORMBase

# ============================================================================
# Вспомогательные классы
# ============================================================================


class RoleNameValidator:
    """Валидатор имени роли (переиспользуемая логика)"""

    @classmethod
    def validate(cls, name: str) -> str:
        """Валидация имени роли"""
        # Нормализация
        name_lower = name.lower().strip()

        # Проверка длины
        if len(name_lower) < 3:
            raise ValueError('Имя роли должно содержать минимум 3 символа')

        # Проверка формата
        if not re.match(r'^[a-z][a-z0-9_]*$', name_lower):
            raise ValueError(
                'Имя роли должно начинаться с буквы и содержать только '
                'латиницу, цифры и подчёркивание'
            )

        return name_lower


# ============================================================================
# Схемы для запросов
# ============================================================================

class RoleCreateRequest(BaseModel):
    """Схема для создания роли"""

    name: Annotated[str, Field(
        min_length=3,
        max_length=50,
        description="Уникальное имя роли (только латиница, цифры, подчёркивание)"
    )]
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Описание роли (необязательно)"
    )

    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация и нормализация имени"""
        return RoleNameValidator.validate(v)

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Очистка описания от лишних пробелов"""
        if v is not None:
            v = v.strip()
            if v == '':
                return None
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "editor",
                "description": "Может редактировать контент"
            }
        }
    )


class RoleUpdateRequest(BaseModel):
    """Схема для частичного обновления роли"""

    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="Новое имя роли"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Новое описание роли"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Валидация и нормализация имени при обновлении"""
        if v is not None:
            return RoleNameValidator.validate(v)
        return v

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'RoleUpdateRequest':
        """Проверяем, что передано хотя бы одно поле для обновления"""
        if not any([self.name, self.description]):
            raise ValueError(
                'Необходимо передать хотя бы одно поле для обновления')
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "senior_editor"},
                {"description": "Старший редактор"},
                {"name": "chief_editor", "description": "Главный редактор"}
            ]
        }
    )


class AssignRoleRequest(BaseModel):
    """Схема для назначения роли пользователю"""

    role_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Имя роли для назначения"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role_name": "manager"
            }
        }
    )


# ============================================================================
# Схемы для ответов
# ============================================================================

class RoleResponse(ORMBase):
    """Схема ответа для одной роли"""

    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "manager",
                "description": "Управляет командой",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class RoleListResponse(BaseModel):
    """Схема ответа для списка ролей с пагинацией"""

    items: List[RoleResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"id": 1, "name": "admin", "description": "Administrator"},
                    {"id": 2, "name": "user", "description": "Regular user"}
                ]
            }
        }
    )


class RoleAssignmentResponse(BaseModel):
    """Схема ответа при назначении роли"""

    user_id: int
    role: RoleResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 5,
                "role": {"id": 2, "name": "manager", "description": "Manager"}
            }
        }
    )


class RoleDeleteResponse(BaseModel):
    """Схема ответа при удалении роли"""

    success: bool
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Роль удалена"
            }
        }
    )
