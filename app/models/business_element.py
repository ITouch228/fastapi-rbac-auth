"""
Модель бизнес элемента.
"""


from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BusinessElement(Base, TimestampMixin):
    """Модель бизнес элемента"""

    __tablename__ = 'business_elements'

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    rules = relationship(
        'AccessRoleRule',
        back_populates='element',
        cascade='all, delete-orphan'
    )

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        **Возвращает:**
            dict: Словарь с данными бизнес элемента
        """
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result

    def __repr__(self) -> str:
        """
        Строковое представление бизнес элемента.

        **Возвращает:**
            str: Строка с ID, name и description бизнес элемента
        """
        return f"<BusinessElement(id={self.id}, name='{self.name}', description='{self.description}')>"
