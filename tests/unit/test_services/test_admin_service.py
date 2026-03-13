"""
Unit тесты для AdminService.

Тестируют бизнес-логику сервиса в изоляции от реальных зависимостей.
Все внешние зависимости (репозитории, БД) заменены на моки.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_rule import AccessRoleRule
from app.models.role import Role
from app.models.user import User
from app.schemas.access_rule import AccessRuleUpdateRequest
from app.schemas.role import RoleCreateRequest, RoleUpdateRequest
from app.services.admin_service import AdminService


class TestAdminService:
    """Unit тесты для AdminService с моками"""

    @pytest.fixture
    def mock_session(self):
        """Мок сессии базы данных"""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def admin_service(self, mock_session):
        """Создание AdminService с моками"""
        service = AdminService(mock_session)
        # Мокаем репозитории
        service.role_repo = AsyncMock()
        service.user_repo = AsyncMock()
        service.rule_repo = AsyncMock()
        return service

    @pytest.fixture
    def sample_role(self):
        """Создание тестовой роли"""
        return Role(
            id=1,
            name="editor",
            description="Editor role"
        )

    @pytest.fixture
    def sample_user(self):
        """Создание тестового пользователя"""
        return User(
            id=1,
            email="user@example.com",
            full_name="Test User",
            is_active=True
        )

    @pytest.fixture
    def sample_rule(self):
        """Создание тестового правила"""
        return AccessRoleRule(
            id=1,
            role_id=1,
            element_id=1,
            read_permission=False,
            create_permission=False,
            update_permission=False,
            delete_permission=False
        )


# ============================================================================
# Тесты для create_role
# ============================================================================


    @pytest.mark.asyncio
    async def test_create_role_success(self, admin_service, mock_session, sample_role):
        """Тест успешного создания роли"""
        payload = RoleCreateRequest(name="editor", description="Editor role")

        # Мокаем проверку на существование
        admin_service.role_repo.get_by_name = AsyncMock(return_value=None)

        # Act
        result = await admin_service.create_role(payload)

        # Assert
        admin_service.role_repo.get_by_name.assert_called_once_with("editor")

        # Проверяем, что session.add был вызван с правильным объектом
        mock_session.add.assert_called_once()
        added_role = mock_session.add.call_args[0][0]
        assert added_role.name == "editor"
        assert added_role.description == "Editor role"

        # Проверяем commit и refresh
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(added_role)

        # Проверяем результат
        assert result == added_role

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, admin_service):
        """Тест создания роли с уже существующим именем -> HTTPException 400"""
        payload = RoleCreateRequest(name="admin", description="Admin role")

        existing_role = Role(id=1, name="admin", description="Existing admin")
        admin_service.role_repo.get_by_name = AsyncMock(
            return_value=existing_role)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.create_role(payload)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
        admin_service.role_repo.create.assert_not_called()


# ============================================================================
# Тесты для assign_role
# ============================================================================


    @pytest.mark.asyncio
    async def test_assign_role_success(self, admin_service, mock_session, sample_user, sample_role):
        """Тест успешного назначения роли пользователю"""
        admin_service.user_repo.get_by_id = AsyncMock(return_value=sample_user)
        admin_service.role_repo.get_by_name = AsyncMock(
            return_value=sample_role)
        admin_service.role_repo.assign_role = AsyncMock()

        result = await admin_service.assign_role(user_id=1, role_name="editor")

        admin_service.user_repo.get_by_id.assert_called_once_with(1)
        admin_service.role_repo.get_by_name.assert_called_once_with("editor")
        admin_service.role_repo.assign_role.assert_called_once_with(1, 1)
        mock_session.commit.assert_called_once()
        assert result == sample_role

    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(self, admin_service):
        """Тест назначения роли несуществующему пользователю -> HTTPException 404"""
        admin_service.user_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.assign_role(user_id=999, role_name="editor")

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
        admin_service.role_repo.assign_role.assert_not_called()

    @pytest.mark.asyncio
    async def test_assign_role_role_not_found(self, admin_service, sample_user):
        """Тест назначения несуществующей роли -> HTTPException 404"""
        admin_service.user_repo.get_by_id = AsyncMock(return_value=sample_user)
        admin_service.role_repo.get_by_name = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.assign_role(user_id=1, role_name="nonexistent")

        assert exc_info.value.status_code == 404
        assert "Role not found" in str(exc_info.value.detail)
        admin_service.role_repo.assign_role.assert_not_called()


# ============================================================================
# Тесты для get_user_roles
# ============================================================================


    @pytest.mark.asyncio
    async def test_get_user_roles_success(self, admin_service, sample_user):
        """Тест успешного получения ролей пользователя"""
        roles = [
            Role(id=1, name="editor", description="Editor"),
            Role(id=2, name="viewer", description="Viewer")
        ]

        admin_service.user_repo.get_by_id = AsyncMock(return_value=sample_user)
        admin_service.role_repo.get_user_roles = AsyncMock(return_value=roles)

        result = await admin_service.get_user_roles(1)

        admin_service.user_repo.get_by_id.assert_called_once_with(1)
        admin_service.role_repo.get_user_roles.assert_called_once_with(1)
        assert len(result) == 2
        assert result[0].name == "editor"
        assert result[1].name == "viewer"

    @pytest.mark.asyncio
    async def test_get_user_roles_user_not_found(self, admin_service):
        """Тест получения ролей несуществующего пользователя -> HTTPException 404"""
        admin_service.user_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.get_user_roles(999)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


# ============================================================================
# Тесты для list_rules
# ============================================================================


    @pytest.mark.asyncio
    async def test_list_rules_success(self, admin_service, sample_rule):
        """Тест успешного получения списка правил"""
        rules = [sample_rule]
        admin_service.rule_repo.list_rules = AsyncMock(return_value=rules)

        result = await admin_service.list_rules()

        admin_service.rule_repo.list_rules.assert_called_once()
        assert len(result) == 1
        assert result[0].id == 1


# ============================================================================
# Тесты для update_rule
# ============================================================================


    @pytest.mark.asyncio
    async def test_update_rule_success(self, admin_service, mock_session, sample_rule):
        """Тест успешного обновления правила"""
        payload = AccessRuleUpdateRequest(
            read_permission=True, create_permission=True)

        admin_service.rule_repo.get_rule = AsyncMock(return_value=sample_rule)

        result = await admin_service.update_rule(1, payload)

        admin_service.rule_repo.get_rule.assert_called_once_with(1)
        assert result.read_permission is True
        assert result.create_permission is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_rule)

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, admin_service):
        """Тест обновления несуществующего правила -> HTTPException 404"""
        payload = AccessRuleUpdateRequest(read_permission=True)
        admin_service.rule_repo.get_rule = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.update_rule(999, payload)

        assert exc_info.value.status_code == 404
        assert "Rule not found" in str(exc_info.value.detail)


# ============================================================================
# Тесты для update_role
# ============================================================================


    @pytest.mark.asyncio
    async def test_update_role_success(self, admin_service, mock_session, sample_role):
        """Тест успешного обновления роли"""
        payload = RoleUpdateRequest(
            name="senior_editor",
            description="Senior editor role"
        )

        admin_service.role_repo.get_by_name = AsyncMock()
        admin_service.role_repo.get_by_name.side_effect = [sample_role, None]

        result = await admin_service.update_role("editor", payload)

        assert result.name == "senior_editor"
        assert result.description == "Senior editor role"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_role)

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, admin_service):
        """Тест обновления несуществующей роли -> HTTPException 404"""
        payload = RoleUpdateRequest(name="new_name")
        admin_service.role_repo.get_by_name = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.update_role("nonexistent", payload)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_role_duplicate_name(self, admin_service, sample_role):
        """Тест обновления роли на имя, которое уже существует -> HTTPException 400"""
        payload = RoleUpdateRequest(name="existing_role")
        existing_role = Role(id=2, name="existing_role",
                             description="Another role")

        admin_service.role_repo.get_by_name = AsyncMock()
        admin_service.role_repo.get_by_name.side_effect = [
            sample_role, existing_role]

        with pytest.raises(HTTPException) as exc_info:
            await admin_service.update_role("editor", payload)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
