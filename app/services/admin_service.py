from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import not_found
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.access_rule import AccessRuleUpdateRequest


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rule_repo = AccessRuleRepository(session)
        self.role_repo = RoleRepository(session)
        self.user_repo = UserRepository(session)

    async def list_rules(self):
        return await self.rule_repo.list_rules()

    async def update_rule(self, rule_id: int, payload: AccessRuleUpdateRequest):
        rule = await self.rule_repo.get_rule(rule_id)
        if rule is None:
            raise not_found('Rule not found')
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(rule, field, value)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def assign_role(self, user_id: int, role_name: str):
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise not_found('User not found')
        role = await self.role_repo.get_by_name(role_name)
        if role is None:
            raise not_found('Role not found')
        await self.role_repo.assign_single_role(user.id, role.id)
        await self.session.commit()
        return role

    async def get_user_roles(self, user_id: int):
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise not_found('User not found')
        return await self.role_repo.get_user_roles(user_id)
