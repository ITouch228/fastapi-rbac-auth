"""
Модель правил доступа роли к бизнес элементу.
"""


from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AccessRoleRule(Base, TimestampMixin):
    """Модель правил доступа"""

    __tablename__ = 'access_role_rules'
    __table_args__ = (
        UniqueConstraint(
            'role_id',
            'element_id',
            name='uq_role_element'
        ),
    )

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            'roles.id',
            ondelete='CASCADE'
        ),
        nullable=False
    )
    element_id: Mapped[int] = mapped_column(
        ForeignKey(
            'business_elements.id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    read_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    read_all_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    create_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    update_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    update_all_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    delete_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    delete_all_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    role = relationship('Role', back_populates='rules')
    element = relationship('BusinessElement', back_populates='rules')

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def __init__(self, **kwargs):
        """Инициализация с значениями по умолчанию"""
        defaults = {
            'read_permission': False,
            'read_all_permission': False,
            'create_permission': False,
            'update_permission': False,
            'update_all_permission': False,
            'delete_permission': False,
            'delete_all_permission': False,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        **Возвращает:**
            dict: Словарь с данными правила доступа
        """
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result

    def __repr__(self) -> str:
        """
        Строковое представление пользователя.

        **Возвращает:**
            str: Строка с ID, role_id и element_id роли
        """
        return f"<AccessRoleRule(id={self.id}, role_id={self.role_id}, element_id={self.element_id})>"
