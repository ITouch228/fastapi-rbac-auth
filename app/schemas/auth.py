"""
Модели Pydantic для работы с авторизацией и токенами.
"""

import re

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class RegisterRequest(BaseModel):
    """Модель запроса на регистрацию пользователя"""

    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_repeat: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Ivan Ivanov",
                "email": "ivan@example.com",
                "password": "StrongPassword123",
                "password_repeat": "StrongPassword123",
            }
        }
    )

    # =========================================================================
    # ВАЛИДАТОРЫ ПОЛЕЙ
    # =========================================================================

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Нормализация email (приведение к нижнему регистру и обрезка пробелов)"""
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """Валидация сложности пароля"""
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^\w\s]", value):
            raise ValueError(
                "Password must contain at least one special character")
        return value

    @model_validator(mode="after")
    def validate_passwords_match(self):
        """Проверка совпадения password и password_repeat"""
        if self.password != self.password_repeat:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    """Модель запроса для логина пользователя"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "ivan@example.com",
                "password": "StrongPassword123"
            }
        }
    )

    # =========================================================================
    # ВАЛИДАТОРЫ ПОЛЕЙ
    # =========================================================================

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Нормализация email (приведение к нижнему регистру и обрезка пробелов)"""
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RefreshRequest(BaseModel):
    """Модель запроса для обновления токена"""

    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class TokenPairResponse(BaseModel):
    """Модель ответа с access и refresh токенами"""

    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )
