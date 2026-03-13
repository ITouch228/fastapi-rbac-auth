from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import AccessRoleRule, BusinessElement, Role


class AccessRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_rules(self) -> list[AccessRoleRule]:
        stmt = select(AccessRoleRule).options(joinedload(AccessRoleRule.role), joinedload(AccessRoleRule.element))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_rule(self, rule_id: int) -> AccessRoleRule | None:
        stmt = (
            select(AccessRoleRule)
            .where(AccessRoleRule.id == rule_id)
            .options(joinedload(AccessRoleRule.role), joinedload(AccessRoleRule.element))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_rules_for_roles_and_element(self, role_ids: list[int], element_name: str) -> list[AccessRoleRule]:
        stmt = (
            select(AccessRoleRule)
            .join(Role, Role.id == AccessRoleRule.role_id)
            .join(BusinessElement, BusinessElement.id == AccessRoleRule.element_id)
            .where(AccessRoleRule.role_id.in_(role_ids), BusinessElement.name == element_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
