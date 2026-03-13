from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_user_roles(self, user_id: int) -> list[Role]:
        stmt = select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_single_role(self, user_id: int, role_id: int) -> None:
        await self.session.execute(delete(UserRole).where(UserRole.user_id == user_id))
        self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.flush()
