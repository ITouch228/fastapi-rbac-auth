"""
Модель роли.
"""


from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    """Модель роли"""

    __tablename__ = 'roles'

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    users = relationship(
        'UserRole',
        back_populates='role',
        cascade='all, delete-orphan'
    )
    rules = relationship(
        'AccessRoleRule',
        back_populates='role',
        cascade='all, delete-orphan'
    )

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        **Возвращает:**
            dict: Словарь с данными роли
        """
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result

    def __repr__(self) -> str:
        """
        Строковое представление пользователя.

        **Возвращает:**
            str: Строка с ID, name и description роли
        """
        return f"<Role(id={self.id}, name='{self.name}', description='{self.description}')>"
