"""
Модель связи пользователя и роли.

Описывает назначение роли пользователю в системе RBAC:
- Связь пользователя с ролью
- Ограничение уникальности пары user_id + role_id
- Связи с моделями User и Role

Используется для:
- Назначения ролей пользователям
- Получения списка ролей пользователя
- Проверки прав доступа через роли
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.role import Role
from app.models.user import User


class UserRole(Base, TimestampMixin):
    """Модель связи пользователя и роли"""

    __tablename__ = 'user_roles'
    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'role_id',
            name='uq_user_role'
        ),
    )

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            'users.id',
            ondelete='CASCADE'
        ),
        nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            'roles.id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    user: Mapped["User"] = relationship(
        'User',
        back_populates='roles'
    )
    role: Mapped["Role"] = relationship(
        'Role',
        back_populates='users'
    )

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        **Возвращает:**
            dict: Словарь с полями модели user-role связи
        """
        result = {}

        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)

        return result

    def __repr__(self) -> str:
        """
        Строковое представление связи пользователя и роли.

        **Возвращает:**
            str: Строка с ID, user_id и role_id
        """
        return (
            f"<UserRole(id={self.id}, user_id={self.user_id}, "
            f"role_id={self.role_id})>"
        )
