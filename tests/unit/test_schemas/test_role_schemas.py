"""
Unit тесты для Pydantic схем ролей.
"""

import pytest
from pydantic import ValidationError

from app.schemas.role import (
    RoleCreateRequest,
    RoleUpdateRequest,
    AssignRoleRequest,
    RoleResponse,
    RoleListResponse,
    RoleAssignmentResponse,
    RoleDeleteResponse,
)


# ============================================================================
# ТЕСТЫ ДЛЯ ROLE CREATE
# ============================================================================

class TestRoleCreateRequest:
    """Unit тесты для RoleCreateRequest"""

    @pytest.mark.unit
    def test_valid_role_create(self):
        """Тест: валидное создание роли."""
        data = {
            "name": "editor",
            "description": "Редактор"
        }

        request = RoleCreateRequest(**data)

        assert request.name == "editor"
        assert request.description == "Редактор"

    @pytest.mark.unit
    def test_name_normalization(self):
        """Тест: имя роли нормализуется (lower + strip)."""
        data = {
            "name": "  Editor  ",
            "description": "Test"
        }

        request = RoleCreateRequest(**data)

        assert request.name == "editor"

    @pytest.mark.unit
    def test_invalid_name_short(self):
        """Тест: имя слишком короткое → ValidationError."""
        data = {"name": "ab"}

        with pytest.raises(ValidationError):
            RoleCreateRequest(**data)

    @pytest.mark.unit
    def test_invalid_name_format(self):
        """Тест: некорректный формат имени → ValidationError."""
        data = {"name": "1invalid"}

        with pytest.raises(ValidationError):
            RoleCreateRequest(**data)

    @pytest.mark.unit
    def test_description_strip(self):
        """Тест: описание очищается от пробелов."""
        data = {
            "name": "editor",
            "description": "   some text   "
        }

        request = RoleCreateRequest(**data)

        assert request.description == "some text"

    @pytest.mark.unit
    def test_description_empty_to_none(self):
        """Тест: пустое описание превращается в None."""
        data = {
            "name": "editor",
            "description": "   "
        }

        request = RoleCreateRequest(**data)

        assert request.description is None


# ============================================================================
# ТЕСТЫ ДЛЯ ROLE UPDATE
# ============================================================================

class TestRoleUpdateRequest:
    """Unit тесты для RoleUpdateRequest"""

    @pytest.mark.unit
    def test_valid_update_name(self):
        """Тест: валидное обновление имени."""
        data = {"name": "manager"}

        request = RoleUpdateRequest(**data)

        assert request.name == "manager"

    @pytest.mark.unit
    def test_valid_update_description(self):
        """Тест: валидное обновление описания."""
        data = {"description": "New description"}

        request = RoleUpdateRequest(**data)

        assert request.description == "New description"

    @pytest.mark.unit
    def test_empty_update(self):
        """Тест: пустой запрос → ValidationError."""
        data = {}

        with pytest.raises(ValidationError) as exc:
            RoleUpdateRequest(**data)

        errors = exc.value.errors()
        assert any("хотя бы одно поле" in err["msg"] for err in errors)

    @pytest.mark.unit
    def test_invalid_name_on_update(self):
        """Тест: невалидное имя при обновлении → ValidationError."""
        data = {"name": "!!invalid"}

        with pytest.raises(ValidationError):
            RoleUpdateRequest(**data)


# ============================================================================
# ТЕСТЫ ДЛЯ ASSIGN ROLE
# ============================================================================

class TestAssignRoleRequest:
    """Unit тесты для AssignRoleRequest"""

    @pytest.mark.unit
    def test_valid_assign(self):
        """Тест: валидное назначение роли."""
        data = {"role_name": "manager"}

        request = AssignRoleRequest(**data)

        assert request.role_name == "manager"

    @pytest.mark.unit
    def test_empty_role_name(self):
        """Тест: пустое имя роли → ValidationError."""
        data = {"role_name": ""}

        with pytest.raises(ValidationError):
            AssignRoleRequest(**data)


# ============================================================================
# ТЕСТЫ ДЛЯ RESPONSE МОДЕЛЕЙ
# ============================================================================

class TestRoleResponse:
    """Unit тесты для RoleResponse"""

    @pytest.mark.unit
    def test_valid_role_response(self):
        """Тест: валидный ответ роли."""
        data = {
            "id": 1,
            "name": "admin",
            "description": "Administrator"
        }

        response = RoleResponse(**data)

        assert response.id == 1
        assert response.name == "admin"


class TestRoleListResponse:
    """Unit тесты для RoleListResponse"""

    @pytest.mark.unit
    def test_valid_role_list(self):
        """Тест: список ролей."""
        data = {
            "items": [
                {"id": 1, "name": "admin", "description": "Admin"},
                {"id": 2, "name": "user", "description": "User"},
            ]
        }

        response = RoleListResponse(**data)

        assert len(response.items) == 2
        assert response.items[0].name == "admin"


class TestRoleAssignmentResponse:
    """Unit тесты для RoleAssignmentResponse"""

    @pytest.mark.unit
    def test_valid_assignment(self):
        """Тест: валидный ответ назначения роли."""
        data = {
            "user_id": 1,
            "role": {"id": 2, "name": "manager", "description": "Manager"}
        }

        response = RoleAssignmentResponse(**data)

        assert response.user_id == 1
        assert response.role.name == "manager"


class TestRoleDeleteResponse:
    """Unit тесты для RoleDeleteResponse"""

    @pytest.mark.unit
    def test_valid_delete_response(self):
        """Тест: валидный ответ удаления роли."""
        data = {
            "success": True,
            "message": "Роль удалена"
        }

        response = RoleDeleteResponse(**data)

        assert response.success is True
        assert response.message == "Роль удалена"
