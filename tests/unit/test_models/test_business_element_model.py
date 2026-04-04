"""
Unit тесты для модели BusinessElement.
"""

from datetime import datetime

import pytest

from app.models.business_element import BusinessElement


class TestBusinessElementModel:
    """Unit тесты для модели BusinessElement"""

    # ========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # ========================================================================

    @pytest.mark.unit
    def test_business_element_creation(self):
        """Тест: создание бизнес-элемента"""
        element = BusinessElement(
            name="users",
            description="User management resource"
        )

        assert element.name == "users"
        assert element.description == "User management resource"
        assert element.id is None

    @pytest.mark.unit
    def test_business_element_creation_without_description(self):
        """Тест: создание элемента без описания"""
        element = BusinessElement(name="products")

        assert element.name == "products"
        assert element.description is None

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_business_element_to_dict(self):
        """Тест: преобразование в словарь"""
        element = BusinessElement(
            name="users",
            description="User management resource"
        )

        element_dict = element.to_dict()

        # Проверяем поля
        assert element_dict["id"] is None
        assert element_dict["name"] == "users"
        assert element_dict["description"] == "User management resource"

    @pytest.mark.unit
    def test_business_element_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        element = BusinessElement(
            name="users",
            description="User management resource",
            created_at=now,
            updated_at=now
        )

        element_dict = element.to_dict()

        assert element_dict["created_at"] == now
        assert element_dict["updated_at"] == now

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ
    # =========================================================================

    @pytest.mark.unit
    def test_business_element_repr(self):
        """Тест: строковое представление"""
        element = BusinessElement(
            name="users",
            description="User management resource"
        )

        repr_str = repr(element)

        assert "BusinessElement" in repr_str
        assert "name='users'" in repr_str
        assert "description='User management resource'" in repr_str

    @pytest.mark.unit
    def test_access_rule_repr_with_id(self):
        """Тест: строковое представление с ID"""
        element = BusinessElement(
            id=1,
            name="users",
            description="User management resource"
        )

        repr_str = repr(element)

        assert "BusinessElement" in repr_str
        assert "id=1" in repr_str
        assert "name='users'" in repr_str
        assert "description='User management resource'" in repr_str

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_business_element_relationships(self):
        """Тест: атрибуты отношений"""
        element = BusinessElement()

        assert hasattr(element, 'rules')
        assert element.rules == []

    @pytest.mark.unit
    def test_timestamp_mixin_fields_exist(self):
        """Тест: наличие полей TimestampMixin"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        element = BusinessElement(
            name="users",
            description="User management resource",
            created_at=now,
            updated_at=now
        )

        assert hasattr(element, 'created_at')
        assert hasattr(element, 'updated_at')
