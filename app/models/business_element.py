from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessElement(Base):
    __tablename__ = 'business_elements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rules = relationship('AccessRoleRule', back_populates='element', cascade='all, delete-orphan')
