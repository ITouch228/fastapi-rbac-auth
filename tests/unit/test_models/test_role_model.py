"""
Unit тесты для модели Role.
"""

from datetime import datetime

import pytest

from app.models.role import Role


class TestRoleModel:
    """Unit тесты для модели Role"""

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # =========================================================================

    @pytest.mark.unit
    def test_role_creation(self):
        """Тест: создание объекта Role со всеми полями"""
        role = Role(
            name="editor",
            description="Can edit content"
        )

        assert role.name == "editor"
        assert role.description == "Can edit content"
        assert role.id is None
        assert role.created_at is None
        assert role.updated_at is None

    @pytest.mark.unit
    def test_role_creation_without_description(self):
        """Тест: создание роли без описания"""
        role = Role(name="viewer")

        assert role.name == "viewer"
        assert role.description is None
        assert role.id is None

    @pytest.mark.unit
    def test_role_creation_minimal(self):
        """Тест: создание роли только с обязательными полями"""
        role = Role(name="admin")

        assert role.name == "admin"
        assert role.description is None

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_role_to_dict(self):
        """Тест: преобразование роли в словарь"""
        role = Role(
            id=1,
            name="editor",
            description="Can edit content"
        )

        role_dict = role.to_dict()

        assert role_dict["id"] == 1
        assert role_dict["name"] == "editor"
        assert role_dict["description"] == "Can edit content"

    @pytest.mark.unit
    def test_role_to_dict_without_id(self):
        """Тест: to_dict без ID (до сохранения в БД)"""
        role = Role(name="editor", description="Editor role")

        role_dict = role.to_dict()

        assert role_dict["id"] is None
        assert role_dict["name"] == "editor"
        assert role_dict["description"] == "Editor role"

    @pytest.mark.unit
    def test_role_to_dict_without_description(self):
        """Тест: to_dict роли без описания"""
        role = Role(id=1, name="viewer")

        role_dict = role.to_dict()

        assert role_dict["id"] == 1
        assert role_dict["name"] == "viewer"
        assert role_dict["description"] is None

    @pytest.mark.unit
    def test_role_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        role = Role(
            id=1,
            name="editor",
            description="Editor role",
            created_at=now,
            updated_at=now
        )

        role_dict = role.to_dict()

        assert role_dict["created_at"] == now
        assert role_dict["updated_at"] == now

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ (__REPR__)
    # =========================================================================

    @pytest.mark.unit
    def test_role_repr(self):
        """Тест: строковое представление"""
        role = Role(id=1, name="editor", description="Can edit content")

        repr_str = repr(role)

        assert "Role" in repr_str
        assert "id=1" in repr_str
        assert "name='editor'" in repr_str
        assert "description='Can edit content'" in repr_str

    @pytest.mark.unit
    def test_role_repr_without_id(self):
        """Тест: строковое представление без ID"""
        role = Role(name="editor", description="Editor role")

        repr_str = repr(role)

        assert "Role" in repr_str
        assert "id=None" in repr_str
        assert "name='editor'" in repr_str
        assert "description='Editor role'" in repr_str

    @pytest.mark.unit
    def test_role_repr_without_description(self):
        """Тест: строковое представление роли без описания"""
        role = Role(id=1, name="viewer")

        repr_str = repr(role)

        assert "Role" in repr_str
        assert "id=1" in repr_str
        assert "name='viewer'" in repr_str
        assert "description='None'" in repr_str

    # =========================================================================
    # ТЕСТЫ СВОЙСТВ (PROPERTIES)
    # =========================================================================

    @pytest.mark.unit
    def test_role_name_property(self):
        """Тест: свойство name"""
        role = Role(name="editor")
        assert role.name == "editor"

        role.name = "senior_editor"
        assert role.name == "senior_editor"

    @pytest.mark.unit
    def test_role_description_property(self):
        """Тест: свойство description"""
        role = Role(description="Test role")
        assert role.description == "Test role"

        role.description = "Updated description"
        assert role.description == "Updated description"

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ (RELATIONSHIPS)
    # =========================================================================

    @pytest.mark.unit
    def test_role_relationships_exist(self):
        """Тест: атрибуты отношений существуют"""
        role = Role(name="editor")

        assert hasattr(role, 'users')
        assert hasattr(role, 'rules')

    @pytest.mark.unit
    def test_role_relationships_default_values(self):
        """Тест: значения по умолчанию для отношений"""
        role = Role(name="editor")

        assert role.users == []
        assert role.rules == []

    # =========================================================================
    # ТЕСТЫ TIMESTAMPMIXIN
    # =========================================================================

    @pytest.mark.unit
    def test_timestamp_mixin_fields_exist(self):
        """Тест: наличие полей TimestampMixin"""
        role = Role(name="editor")

        assert hasattr(role, 'created_at')
        assert hasattr(role, 'updated_at')

    @pytest.mark.unit
    def test_timestamp_mixin_default_values(self):
        """Тест: значения по умолчанию для TimestampMixin"""
        role = Role(name="editor")

        assert role.created_at is None
        assert role.updated_at is None

    # =========================================================================
    # ТЕСТЫ ТИПОВ ДАННЫХ
    # =========================================================================

    @pytest.mark.unit
    def test_role_field_types(self):
        """Тест: типы полей модели"""
        role = Role(id=1, name="editor", description="Editor role")

        assert isinstance(role.id, int)
        assert isinstance(role.name, str)
        assert isinstance(role.description, str) or role.description is None

    # =========================================================================
    # ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_role_name_min_length(self):
        """Тест: имя роли минимальной длины"""
        role = Role(name="a")
        assert len(role.name) == 1

    @pytest.mark.unit
    def test_role_name_max_length(self):
        """Тест: имя роли максимальной длины"""
        long_name = "a" * 64
        role = Role(name=long_name)
        assert len(role.name) == 64

    @pytest.mark.unit
    def test_role_description_max_length(self):
        """Тест: описание роли максимальной длины"""
        long_description = "A" * 255
        role = Role(name="editor", description=long_description)
        assert len(role.description) == 255

    @pytest.mark.unit
    def test_role_name_with_underscore(self):
        """Тест: имя роли с подчёркиванием"""
        role = Role(name="senior_editor")
        assert role.name == "senior_editor"

    @pytest.mark.unit
    def test_role_name_with_digits(self):
        """Тест: имя роли с цифрами"""
        role = Role(name="role_123")
        assert role.name == "role_123"
