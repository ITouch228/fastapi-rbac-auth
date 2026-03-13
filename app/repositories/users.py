from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email).options(selectinload(User.roles).selectinload(UserRole.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles).selectinload(UserRole.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, *, full_name: str, email: str, password_hash: str) -> User:
        user = User(full_name=full_name, email=email, password_hash=password_hash, is_active=True)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_profile(self, user: User, *, full_name: str | None, email: str | None) -> User:
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        await self.session.flush()
        return user

    async def soft_delete(self, user: User) -> User:
        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return user
