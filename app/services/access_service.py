"""
Сервис для проверки прав доступа.

Обрабатывает авторизацию пользователей на основе их ролей и правил доступа.
Поддерживает различные действия (чтение, создание, обновление, удаление)
и различает доступ к своим и чужим ресурсам.
"""

from enum import Enum
from typing import List

from app.core.exceptions import forbidden, unauthorized
from app.models import AccessRoleRule, User
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository


class Action(str, Enum):
    """
    Действия, которые могут быть выполнены над ресурсами.

    Attributes:
        READ: Чтение ресурса
        CREATE: Создание нового ресурса
        UPDATE: Обновление существующего ресурса
        DELETE: Удаление ресурса
    """
    READ = 'read'
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class AccessService:
    """
    Сервис для проверки прав доступа.

    Реализует логику авторизации на основе RBAC (Role-Based Access Control):
    - Проверяет аутентификацию пользователя
    - Получает роли пользователя
    - Проверяет права доступа на основе правил
    - Различает доступ к своим и чужим ресурсам
    """

    def __init__(self, role_repo: RoleRepository, rule_repo: AccessRuleRepository) -> None:
        """
        Инициализация сервиса доступа.

        Args:
            role_repo: Репозиторий для работы с ролями
            rule_repo: Репозиторий для работы с правилами доступа
        """
        self.role_repo = role_repo
        self.rule_repo = rule_repo

    # =========================================================================
    # Публичные методы
    # =========================================================================

    async def check_access(
        self,
        *,
        user: User | None,
        element_name: str,
        action: Action,
        resource_owner_id: int | None = None,
    ) -> None:
        """
        Проверяет, имеет ли пользователь право на выполнение действия.

        Алгоритм проверки:
        1. Проверка аутентификации и активности пользователя
        2. Получение всех ролей пользователя
        3. Если ролей нет — доступ запрещён
        4. Получение правил доступа для ролей и ресурса
        5. Проверка, есть ли хотя бы одно правило, дающее доступ
        6. Если доступа нет — выбрасывается исключение

        Args:
            user: Текущий пользователь (может быть None)
            element_name: Название бизнес-элемента (ресурса)
            action: Выполняемое действие
            resource_owner_id: ID владельца ресурса (для проверки доступа к своим ресурсам)

        Raises:
            HTTPException 401: Пользователь не аутентифицирован или неактивен
            HTTPException 403: Недостаточно прав (нет ролей или правил)

        Example:
            await access_service.check_access(
                user=current_user,
                element_name="users",
                action=Action.UPDATE,
                resource_owner_id=user.id
            )
        """
        # Шаг 1: Проверка аутентификации
        if user is None or not user.is_active:
            raise unauthorized()

        # Шаг 2: Получение ролей пользователя
        roles = await self.role_repo.get_user_roles(user.id)
        role_ids = [role.id for role in roles]

        # Шаг 3: Если нет ролей — доступ запрещён
        if not role_ids:
            raise forbidden('User has no roles assigned')

        # Шаг 4: Получение правил доступа для ролей и ресурса
        rules = await self.rule_repo.get_rules_for_roles_and_element(
            role_ids,
            element_name
        )

        # Шаг 5: Проверка наличия разрешающего правила
        if self._is_allowed(
            rules=rules,
            user_id=user.id,
            action=action,
            resource_owner_id=resource_owner_id
        ):
            return

        # Шаг 6: Доступ запрещён
        raise forbidden()

    # =========================================================================
    # Приватные методы
    # =========================================================================

    def _is_allowed(
        self,
        *,
        rules: List[AccessRoleRule],
        user_id: int,
        action: Action,
        resource_owner_id: int | None
    ) -> bool:
        """
        Проверяет, разрешено ли действие на основе правил.

        Логика проверки:
        1. Правила обрабатываются по очереди (OR логика)
        2. Если есть правило с правом на все ресурсы (read_all, update_all, delete_all) — доступ разрешён
        3. Если есть правило с правом на свои ресурсы (read, update, delete):
           - Для CREATE: доступ разрешён всегда
           - Для других действий: требуется совпадение resource_owner_id с user_id

        Args:
            rules: Список правил доступа для ролей пользователя
            user_id: ID текущего пользователя
            action: Выполняемое действие
            resource_owner_id: ID владельца ресурса (None для создания)

        Returns:
            bool: True если доступ разрешён, False в противном случае
        """
        # Маппинг действий на названия полей в модели AccessRoleRule
        own_permission_map = {
            Action.READ: 'read_permission',
            Action.CREATE: 'create_permission',
            Action.UPDATE: 'update_permission',
            Action.DELETE: 'delete_permission',
        }

        # Маппинг действий на права доступа ко всем ресурсам
        # CREATE не имеет all_permission, так как создание всегда индивидуально
        all_permission_map = {
            Action.READ: 'read_all_permission',
            Action.CREATE: None,
            Action.UPDATE: 'update_all_permission',
            Action.DELETE: 'delete_all_permission',
        }

        # Перебираем все правила (достаточно одного разрешающего)
        for rule in rules:
            # Проверка права на доступ ко всем ресурсам (например, read_all_permission)
            all_permission_field = all_permission_map[action]
            if all_permission_field and getattr(rule, all_permission_field):
                return True  # Доступ ко всем ресурсам разрешён

            # Проверка права на доступ к своим ресурсам
            own_permission_field = own_permission_map[action]
            if getattr(rule, own_permission_field):
                # Для создания ресурса: право есть всегда
                if action is Action.CREATE:
                    return True

                # Для остальных действий: проверяем, что ресурс принадлежит пользователю
                if resource_owner_id is not None and resource_owner_id == user_id:
                    return True

        return False  # Ни одно правило не разрешило доступ
