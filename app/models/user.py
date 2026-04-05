"""
Модель пользователя.

Описывает пользователя системы RBAC:
- Основные данные пользователя
- Статус активности
- Признак мягкого удаления
- Связи с ролями и refresh token

Используется для:
- Аутентификации и авторизации
- Управления профилем пользователя
- Назначения ролей
- Хранения истории refresh token
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Модель пользователя"""

    __tablename__ = 'users'

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    roles = relationship(
        'UserRole',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    refresh_tokens = relationship(
        'RefreshToken',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def __init__(self, **kwargs):
        """
        Инициализация модели с значениями по умолчанию.

        **Значения по умолчанию:**
            - **is_active**: True
            - **deleted_at**: None
        """
        defaults = {
            'is_active': True,
            'deleted_at': None,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def soft_delete(self) -> None:
        """
        Мягкое удаление пользователя.

        Деактивирует пользователя и устанавливает
        дату мягкого удаления.
        """
        if self.is_active:
            self.is_active = False
            self.deleted_at = datetime.now()

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        Исключает чувствительные данные пользователя
        из результирующего словаря.

        **Возвращает:**
            dict: Словарь с данными пользователя без password_hash
        """
        result = {}

        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)

        # Исключаем чувствительные данные
        result.pop('password_hash', None)
        return result

    def __repr__(self) -> str:
        """
        Строковое представление пользователя.

        **Возвращает:**
            str: Строка с ID, email и full_name пользователя
        """
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"full_name='{self.full_name}')>"
        )
