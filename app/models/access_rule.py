from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccessRoleRule(Base):
    __tablename__ = 'access_role_rules'
    __table_args__ = (UniqueConstraint('role_id', 'element_id', name='uq_role_element'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    element_id: Mapped[int] = mapped_column(ForeignKey('business_elements.id', ondelete='CASCADE'), nullable=False)

    read_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_all_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    create_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    update_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    update_all_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delete_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delete_all_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role = relationship('Role', back_populates='rules')
    element = relationship('BusinessElement', back_populates='rules')
