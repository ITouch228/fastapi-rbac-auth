"""
Unit тесты для модели User.
Тестируют только логику модели, без БД.
"""

from datetime import datetime

import pytest

from app.models.user import User


class TestUserModel:
    """Unit тесты для модели User"""

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # =========================================================================

    @pytest.mark.unit
    def test_user_creation(self):
        """Тест: создание объекта User со всеми полями"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password_123",
            is_active=True
        )

        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.password_hash == "hashed_password_123"
        assert user.is_active is True
        assert user.id is None
        assert user.created_at is None
        assert user.updated_at is None
        assert user.deleted_at is None

    @pytest.mark.unit
    def test_user_creation_without_full_name(self):
        """Тест: создание пользователя без имени (full_name необязателен?)"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )

        assert user.email == "test@example.com"
        assert user.full_name is None
        assert user.is_active is True

    @pytest.mark.unit
    def test_user_creation_default_values(self):
        """Тест: значения по умолчанию"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        assert user.is_active is True
        assert user.deleted_at is None

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_user_to_dict(self):
        """Тест: преобразование в словарь (исключая пароль)"""
        user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash="secret_hash",
            is_active=True
        )

        user_dict = user.to_dict()

        # Проверяем, что password_hash исключён
        assert "password_hash" not in user_dict

        # Проверяем остальные поля
        assert user_dict["id"] == 1
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["is_active"] is True

    @pytest.mark.unit
    def test_user_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            created_at=now,
            updated_at=now
        )

        user_dict = user.to_dict()

        assert user_dict["created_at"] == now
        assert user_dict["updated_at"] == now

    @pytest.mark.unit
    def test_user_to_dict_with_none_values(self):
        """Тест: to_dict с None значениями"""
        user = User(
            id=1,
            email="test@example.com",
            full_name=None,
            is_active=True
        )

        user_dict = user.to_dict()

        assert user_dict["full_name"] is None
        assert user_dict["deleted_at"] is None

    # =========================================================================
    # ТЕСТЫ МЯГКОГО УДАЛЕНИЯ (SOFT DELETE)
    # =========================================================================

    @pytest.mark.unit
    def test_soft_delete(self):
        """Тест: мягкое удаление активного пользователя"""
        user = User(is_active=True, deleted_at=None)

        user.soft_delete()

        assert user.is_active is False
        assert user.deleted_at is not None

    @pytest.mark.unit
    def test_soft_delete_already_deleted(self):
        """Тест: повторное мягкое удаление (не меняет состояние)"""
        deleted_at = datetime(2024, 1, 1, 12, 0, 0)
        user = User(is_active=False, deleted_at=deleted_at)

        user.soft_delete()

        assert user.is_active is False
        assert user.deleted_at == deleted_at

    @pytest.mark.unit
    def test_soft_delete_inactive_user(self):
        """Тест: мягкое удаление неактивного пользователя"""
        user = User(is_active=False)

        user.soft_delete()

        assert user.is_active is False
        assert user.deleted_at is None

    # =========================================================================
    # ТЕСТЫ СВОЙСТВ (PROPERTIES)
    # =========================================================================

    @pytest.mark.unit
    def test_is_active_property(self):
        """Тест: свойство is_active"""
        user = User(is_active=True)
        assert user.is_active is True

        user.is_active = False
        assert user.is_active is False

    @pytest.mark.unit
    def test_email_property(self):
        """Тест: свойство email"""
        user = User(email="test@example.com")
        assert user.email == "test@example.com"

        user.email = "new@example.com"
        assert user.email == "new@example.com"

    @pytest.mark.unit
    def test_full_name_property(self):
        """Тест: свойство full_name"""
        user = User(full_name="Test User")
        assert user.full_name == "Test User"

        user.full_name = "Updated Name"
        assert user.full_name == "Updated Name"

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ (__REPR__)
    # =========================================================================

    @pytest.mark.unit
    def test_user_repr(self):
        """Тест: строковое представление с ID"""
        user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        repr_str = repr(user)

        assert "User" in repr_str
        assert "id=1" in repr_str
        assert "test@example.com" in repr_str
        assert "Test User" in repr_str

    @pytest.mark.unit
    def test_user_repr_without_id(self):
        """Тест: строковое представление без ID"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        repr_str = repr(user)

        assert "User" in repr_str
        assert "id=None" in repr_str
        assert "test@example.com" in repr_str
        assert "Test User" in repr_str

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ (RELATIONSHIPS)
    # =========================================================================

    @pytest.mark.unit
    def test_user_relationships_exist(self):
        """Тест: атрибуты отношений существуют"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        assert hasattr(user, 'roles')
        assert hasattr(user, 'refresh_tokens')

    @pytest.mark.unit
    def test_user_relationships_default_values(self):
        """Тест: значения по умолчанию для отношений"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        assert user.roles == []
        assert user.refresh_tokens == []

    # =========================================================================
    # ТЕСТЫ TIMESTAMPMIXIN
    # =========================================================================

    @pytest.mark.unit
    def test_timestamp_mixin_fields_exist(self):
        """Тест: наличие полей TimestampMixin"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')

    @pytest.mark.unit
    def test_timestamp_mixin_default_values(self):
        """Тест: значения по умолчанию для TimestampMixin"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hash"
        )

        assert user.created_at is None
        assert user.updated_at is None

    # =========================================================================
    # ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_email_max_length(self):
        """Тест: email максимальной длины"""
        long_email = "a" * 200 + "@example.com"
        user = User(
            email=long_email,
            full_name="Test",
            password_hash="hash"
        )
        assert len(user.email) == len(long_email)

    @pytest.mark.unit
    def test_full_name_max_length(self):
        """Тест: full_name максимальной длины"""
        long_name = "A" * 255
        user = User(
            email="test@example.com",
            full_name=long_name,
            password_hash="hash"
        )
        assert len(user.full_name) == 255

    @pytest.mark.unit
    def test_email_min_length(self):
        """Тест: email минимальной длины"""
        short_email = "a@b.c"
        user = User(
            email=short_email,
            full_name="Test",
            password_hash="hash"
        )
        assert len(user.email) == len(short_email)
