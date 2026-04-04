"""
Unit тесты для модели UserRole.
"""

from datetime import datetime

import pytest

from app.models.user_role import UserRole


class TestUserRoleModel:
    """Unit тесты для модели UserRole"""

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_creation(self):
        """Тест: создание связи пользователь-роль"""
        user_role = UserRole(
            user_id=1,
            role_id=2
        )

        assert user_role.user_id == 1
        assert user_role.role_id == 2
        assert user_role.id is None

    @pytest.mark.unit
    def test_user_role_creation_without_id(self):
        """Тест: создание связи без указания ID"""
        user_role = UserRole(user_id=5, role_id=10)

        assert user_role.user_id == 5
        assert user_role.role_id == 10
        assert user_role.id is None

    @pytest.mark.unit
    def test_user_role_creation_with_negative_ids(self):
        """Тест: создание связи с отрицательными ID"""
        user_role = UserRole(user_id=-1, role_id=-2)

        assert user_role.user_id == -1
        assert user_role.role_id == -2
        assert user_role.id is None

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_to_dict(self):
        """Тест: преобразование в словарь"""
        user_role = UserRole(
            id=1,
            user_id=5,
            role_id=10
        )

        user_role_dict = user_role.to_dict()

        assert user_role_dict["id"] == 1
        assert user_role_dict["user_id"] == 5
        assert user_role_dict["role_id"] == 10

    @pytest.mark.unit
    def test_user_role_to_dict_without_id(self):
        """Тест: to_dict без ID"""
        user_role = UserRole(user_id=5, role_id=10)

        user_role_dict = user_role.to_dict()

        assert user_role_dict["id"] is None
        assert user_role_dict["user_id"] == 5
        assert user_role_dict["role_id"] == 10

    @pytest.mark.unit
    def test_user_role_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        user_role = UserRole(
            id=1,
            user_id=5,
            role_id=10,
            created_at=now,
            updated_at=now
        )

        user_role_dict = user_role.to_dict()

        assert user_role_dict["created_at"] == now
        assert user_role_dict["updated_at"] == now

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ (__REPR__)
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_repr(self):
        """Тест: строковое представление"""
        user_role = UserRole(user_id=1, role_id=2)

        repr_str = repr(user_role)

        assert "UserRole" in repr_str
        assert "user_id=1" in repr_str
        assert "role_id=2" in repr_str

    @pytest.mark.unit
    def test_user_role_repr_with_id(self):
        """Тест: строковое представление с ID"""
        user_role = UserRole(id=10, user_id=1, role_id=2)

        repr_str = repr(user_role)

        assert "UserRole" in repr_str
        assert "id=10" in repr_str
        assert "user_id=1" in repr_str
        assert "role_id=2" in repr_str

    @pytest.mark.unit
    def test_user_role_repr_without_id(self):
        """Тест: строковое представление без ID"""
        user_role = UserRole(user_id=1, role_id=2)

        repr_str = repr(user_role)

        assert "UserRole" in repr_str
        assert "id=None" in repr_str
        assert "user_id=1" in repr_str
        assert "role_id=2" in repr_str

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ (RELATIONSHIPS)
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_relationships_exist(self):
        """Тест: атрибуты отношений существуют"""
        user_role = UserRole()

        assert hasattr(user_role, 'user')
        assert hasattr(user_role, 'role')

    @pytest.mark.unit
    def test_user_role_relationships_default_values(self):
        """Тест: значения по умолчанию для отношений"""
        user_role = UserRole()

        assert user_role.user is None
        assert user_role.role is None

    # =========================================================================
    # ТЕСТЫ ТИПОВ ДАННЫХ
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_foreign_keys_types(self):
        """Тест: типы внешних ключей"""
        user_role = UserRole(user_id=1, role_id=2)

        assert isinstance(user_role.user_id, int)
        assert isinstance(user_role.role_id, int)

    @pytest.mark.unit
    def test_user_role_id_type(self):
        """Тест: тип ID"""
        user_role = UserRole(user_id=1, role_id=2)

        assert user_role.id is None or isinstance(user_role.id, int)

    # =========================================================================
    # ТЕСТЫ TIMESTAMPMIXIN
    # =========================================================================

    @pytest.mark.unit
    def test_timestamp_mixin_fields_exist(self):
        """Тест: наличие полей TimestampMixin"""
        user_role = UserRole(user_id=1, role_id=2)

        assert hasattr(user_role, 'created_at')
        assert hasattr(user_role, 'updated_at')

    @pytest.mark.unit
    def test_timestamp_mixin_default_values(self):
        """Тест: значения по умолчанию для TimestampMixin"""
        user_role = UserRole(user_id=1, role_id=2)

        assert user_role.created_at is None
        assert user_role.updated_at is None

    # =========================================================================
    # ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_minimum_values(self):
        """Тест: минимальные значения ID"""
        user_role = UserRole(user_id=1, role_id=1)

        assert user_role.user_id == 1
        assert user_role.role_id == 1

    @pytest.mark.unit
    def test_user_role_maximum_values(self):
        """Тест: максимальные значения ID (большие числа)"""
        large_id = 9223372036854775807
        user_role = UserRole(user_id=large_id, role_id=large_id)

        assert user_role.user_id == large_id
        assert user_role.role_id == large_id

    # =========================================================================
    # ТЕСТЫ УНИКАЛЬНОСТИ (ЛОГИКА, НЕ БД)
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_equality_based_on_ids(self):
        """Тест: сравнение связей по user_id и role_id"""
        user_role1 = UserRole(user_id=1, role_id=2)
        user_role2 = UserRole(user_id=1, role_id=2)

        assert user_role1.user_id == user_role2.user_id
        assert user_role1.role_id == user_role2.role_id

    @pytest.mark.unit
    def test_user_role_different_combinations(self):
        """Тест: разные комбинации пользователь-роль"""
        user_role1 = UserRole(user_id=1, role_id=2)
        user_role2 = UserRole(user_id=1, role_id=3)
        user_role3 = UserRole(user_id=2, role_id=2)

        assert user_role1.user_id == user_role2.user_id
        assert user_role1.role_id != user_role2.role_id
        assert user_role1.user_id != user_role3.user_id
        assert user_role1.role_id == user_role3.role_id

    # =========================================================================
    # ТЕСТЫ МЕТОДА TO_DICT С РАЗНЫМИ СЦЕНАРИЯМИ
    # =========================================================================

    @pytest.mark.unit
    def test_user_role_to_dict_with_none_values(self):
        """Тест: to_dict с None значениями"""
        user_role = UserRole(user_id=1, role_id=2)

        user_role_dict = user_role.to_dict()

        assert user_role_dict["id"] is None
        assert user_role_dict["created_at"] is None
        assert user_role_dict["updated_at"] is None

    @pytest.mark.unit
    def test_user_role_to_dict_all_fields_none(self):
        """Тест: to_dict когда все поля None"""
        user_role = UserRole()

        user_role_dict = user_role.to_dict()

        assert user_role_dict["id"] is None
        assert user_role_dict["user_id"] is None
        assert user_role_dict["role_id"] is None
