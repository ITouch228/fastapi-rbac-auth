from enum import Enum

from app.core.exceptions import forbidden, unauthorized
from app.models import User
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository


class Action(str, Enum):
    READ = 'read'
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class AccessService:
    def __init__(self, role_repo: RoleRepository, rule_repo: AccessRuleRepository) -> None:
        self.role_repo = role_repo
        self.rule_repo = rule_repo

    async def check_access(
        self,
        *,
        user: User | None,
        element_name: str,
        action: Action,
        resource_owner_id: int | None = None,
    ) -> None:
        if user is None or not user.is_active:
            raise unauthorized()

        roles = await self.role_repo.get_user_roles(user.id)
        role_ids = [role.id for role in roles]
        if not role_ids:
            raise forbidden('User has no roles assigned')

        rules = await self.rule_repo.get_rules_for_roles_and_element(role_ids, element_name)
        if self._is_allowed(rules=rules, user_id=user.id, action=action, resource_owner_id=resource_owner_id):
            return
        raise forbidden()

    def _is_allowed(self, *, rules, user_id: int, action: Action, resource_owner_id: int | None) -> bool:
        own_map = {
            Action.READ: 'read_permission',
            Action.CREATE: 'create_permission',
            Action.UPDATE: 'update_permission',
            Action.DELETE: 'delete_permission',
        }
        all_map = {
            Action.READ: 'read_all_permission',
            Action.CREATE: None,
            Action.UPDATE: 'update_all_permission',
            Action.DELETE: 'delete_all_permission',
        }

        for rule in rules:
            all_field = all_map[action]
            if all_field and getattr(rule, all_field):
                return True
            if getattr(rule, own_map[action]):
                if action is Action.CREATE:
                    return True
                if resource_owner_id is not None and resource_owner_id == user_id:
                    return True
        return False
