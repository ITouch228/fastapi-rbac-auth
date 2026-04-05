from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Role, UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_user_roles(self, user_id: int) -> list[Role]:
        stmt = select(Role).join(
            UserRole,
            UserRole.role_id == Role.id
        ).where(UserRole.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_role(self, user_id: int, role_id: int) -> None:
        existing = await self.session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(UserRole(user_id=user_id, role_id=role_id))
            await self.session.flush()
