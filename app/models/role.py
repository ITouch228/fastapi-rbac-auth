from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users = relationship('UserRole', back_populates='role', cascade='all, delete-orphan')
    rules = relationship('AccessRoleRule', back_populates='role', cascade='all, delete-orphan')
