"""
Базовые классы ORM моделей.

Содержит:
- Базовый декларативный класс для всех моделей
- Mixin с временными метками создания и обновления записи

Используется для:
- Наследования всеми ORM моделями приложения
- Унификации общих полей моделей
- Автоматического хранения created_at и updated_at
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый декларативный класс для ORM моделей"""


class TimestampMixin:
    """Mixin с временными метками создания и обновления"""

    # =========================================================================
    # ОБЩИЕ ПОЛЯ ВРЕМЕННЫХ МЕТОК
    # =========================================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
