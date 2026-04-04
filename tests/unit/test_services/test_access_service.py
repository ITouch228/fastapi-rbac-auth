"""
Unit тесты для AccessService.

Тестируют бизнес-логику проверки прав доступа в изоляции от реальных зависимостей.
Все внешние зависимости (репозитории) заменены на моки.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.access_rule import AccessRoleRule
from app.models.role import Role
from app.models.user import User
from app.services.access_service import AccessService, Action


class TestAccessService:
    """Unit тесты для AccessService с моками"""

    @pytest.fixture
    def mock_role_repo(self):
        """Мок репозитория ролей"""
        return AsyncMock()

    @pytest.fixture
    def mock_rule_repo(self):
        """Мок репозитория правил"""
        return AsyncMock()

    @pytest.fixture
    def access_service(self, mock_role_repo, mock_rule_repo):
        """Создание AccessService с моками"""
        return AccessService(mock_role_repo, mock_rule_repo)

    @pytest.fixture
    def sample_user(self):
        """Создание тестового пользователя"""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )

    @pytest.fixture
    def inactive_user(self):
        """Создание неактивного пользователя"""
        return User(
            id=2,
            email="inactive@example.com",
            full_name="Inactive User",
            is_active=False
        )

    @pytest.fixture
    def sample_roles(self):
        """Создание тестовых ролей"""
        return [
            Role(id=1, name="editor", description="Editor role"),
            Role(id=2, name="viewer", description="Viewer role")
        ]

    @pytest.fixture
    def sample_rules_with_read_permission(self):
        """Создание правил с правом на чтение"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=True,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_read_all_permission(self):
        """Создание правил с правом на чтение всех"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=True,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_create_permission(self):
        """Создание правил с правом на создание"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=True,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_update_permission(self):
        """Создание правил с правом на обновление своих ресурсов"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=True,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_update_all_permission(self):
        """Создание правил с правом на обновление всех ресурсов"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=True,
                delete_permission=False,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_delete_permission(self):
        """Создание правил с правом на удаление своих ресурсов"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=True,
                delete_all_permission=False
            )
        ]

    @pytest.fixture
    def sample_rules_with_delete_all_permission(self):
        """Создание правил с правом на удаление всех ресурсов"""
        return [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=True
            )
        ]


# ============================================================================
# Тесты для check_access - аутентификация
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_user_none(self, access_service):
        """
        Тест: пользователь None -> Unauthorized.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=None,
                element_name="users",
                action=Action.READ
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_check_access_user_inactive(self, access_service, inactive_user):
        """
        Тест: неактивный пользователь -> Unauthorized.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=inactive_user,
                element_name="users",
                action=Action.READ
            )

        assert exc_info.value.status_code == 401


# ============================================================================
# Тесты для check_access - роли
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_no_roles(self, access_service, mock_role_repo, sample_user):
        """
        Тест: пользователь без ролей -> Forbidden.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.READ
            )

        assert exc_info.value.status_code == 403
        assert "User has no roles assigned" in str(exc_info.value.detail)


# ============================================================================
# Тесты для check_access - READ permission
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_read_own_resource_success(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_read_permission
    ):
        """
        Тест: чтение своего ресурса с правом read_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_read_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.READ,
            resource_owner_id=sample_user.id  # свой ресурс
        )

        # Assert - не должно быть исключения
        mock_role_repo.get_user_roles.assert_called_once_with(1)
        mock_rule_repo.get_rules_for_roles_and_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_access_read_own_resource_no_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles
    ):
        """
        Тест: чтение своего ресурса без права read_permission -> Forbidden.
        """
        # Arrange
        rules_without_read = [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=rules_without_read)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.READ,
                resource_owner_id=sample_user.id
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_check_access_read_all_resources_success(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_read_all_permission
    ):
        """
        Тест: чтение чужого ресурса с правом read_all_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_read_all_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.READ,
            resource_owner_id=999  # чужой ресурс
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_read_other_resource_without_all_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_read_permission
    ):
        """
        Тест: чтение чужого ресурса без read_all_permission -> Forbidden.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_read_permission)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.READ,
                resource_owner_id=999  # чужой ресурс
            )

        assert exc_info.value.status_code == 403


# ============================================================================
# Тесты для check_access - CREATE permission
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_create_success(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_create_permission
    ):
        """
        Тест: создание ресурса с правом create_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_create_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.CREATE,
            resource_owner_id=None  # для создания resource_owner_id не нужен
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_create_no_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_read_permission
    ):
        """
        Тест: создание ресурса без права create_permission -> Forbidden.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_read_permission)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.CREATE
            )

        assert exc_info.value.status_code == 403


# ============================================================================
# Тесты для check_access - UPDATE permission
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_update_own_resource_success(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_update_permission
    ):
        """
        Тест: обновление своего ресурса с правом update_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_update_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.UPDATE,
            resource_owner_id=sample_user.id
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_update_other_resource_with_all_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_update_all_permission
    ):
        """
        Тест: обновление чужого ресурса с правом update_all_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_update_all_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.UPDATE,
            resource_owner_id=999
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_update_other_resource_without_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_update_permission
    ):
        """
        Тест: обновление чужого ресурса без update_all_permission -> Forbidden.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_update_permission)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.UPDATE,
                resource_owner_id=999
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_check_access_update_own_resource_no_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles
    ):
        """
        Тест: обновление своего ресурса без права update_permission -> Forbidden.
        """
        # Arrange
        rules_without_update = [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=True,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=rules_without_update)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.UPDATE,
                resource_owner_id=sample_user.id
            )

        assert exc_info.value.status_code == 403


# ============================================================================
# Тесты для check_access - DELETE permission
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_delete_own_resource_success(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_delete_permission
    ):
        """
        Тест: удаление своего ресурса с правом delete_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_delete_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.DELETE,
            resource_owner_id=sample_user.id
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_delete_other_resource_with_all_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_delete_all_permission
    ):
        """
        Тест: удаление чужого ресурса с правом delete_all_permission -> разрешено.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_delete_all_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.DELETE,
            resource_owner_id=999
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_delete_other_resource_without_permission(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_delete_permission
    ):
        """
        Тест: удаление чужого ресурса без delete_all_permission -> Forbidden.
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_delete_permission)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.DELETE,
                resource_owner_id=999
            )

        assert exc_info.value.status_code == 403


# ============================================================================
# Тесты для _is_allowed (private метод, тестируем через check_access)
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_multiple_rules_first_matches(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles
    ):
        """
        Тест: несколько правил, первое подходит.
        """
        # Arrange
        rules = [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=True,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            ),
            AccessRoleRule(
                id=2,
                role_id=2,
                element_id=1,
                read_permission=False,
                read_all_permission=True,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=rules)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.READ,
            resource_owner_id=sample_user.id
        )

        # Assert - не должно быть исключения

    @pytest.mark.asyncio
    async def test_check_access_multiple_rules_second_matches(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles
    ):
        """
        Тест: несколько правил, второе подходит.
        """
        # Arrange
        rules = [
            AccessRoleRule(
                id=1,
                role_id=1,
                element_id=1,
                read_permission=False,
                read_all_permission=False,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            ),
            AccessRoleRule(
                id=2,
                role_id=2,
                element_id=1,
                read_permission=False,
                read_all_permission=True,
                create_permission=False,
                update_permission=False,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False
            )
        ]
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=rules)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.READ,
            resource_owner_id=999  # чужой ресурс
        )

        # Assert - не должно быть исключения


# ============================================================================
# Тесты для check_access - разные resource_owner_id
# ============================================================================


    @pytest.mark.asyncio
    async def test_check_access_resource_owner_id_none_for_read(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_read_permission
    ):
        """
        Тест: чтение без resource_owner_id (не указан владелец) -> Forbidden
        (так как read_permission требует resource_owner_id == user_id)
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_read_permission)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await access_service.check_access(
                user=sample_user,
                element_name="users",
                action=Action.READ,
                resource_owner_id=None
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_check_access_resource_owner_id_none_for_create(
        self, access_service, mock_role_repo, mock_rule_repo, sample_user, sample_roles, sample_rules_with_create_permission
    ):
        """
        Тест: создание без resource_owner_id -> разрешено (create не требует владельца).
        """
        # Arrange
        mock_role_repo.get_user_roles = AsyncMock(return_value=sample_roles)
        mock_rule_repo.get_rules_for_roles_and_element = AsyncMock(
            return_value=sample_rules_with_create_permission)

        # Act
        await access_service.check_access(
            user=sample_user,
            element_name="users",
            action=Action.CREATE,
            resource_owner_id=None
        )

        # Assert - не должно быть исключения
