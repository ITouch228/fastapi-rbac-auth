"""
Unit тесты для модели AccessRoleRule.
Описание: тестируют логику модели без БД.
"""

from datetime import datetime

import pytest

from app.models.access_rule import AccessRoleRule


class TestAccessRuleModel:
    """Unit тесты для модели AccessRoleRule"""

    # ========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # ========================================================================

    @pytest.mark.unit
    def test_access_rule_creation(self):
        """Тест: создание правила доступа"""
        rule = AccessRoleRule(
            role_id=1,
            element_id=2,
            read_permission=True,
            create_permission=False,
            update_permission=True,
            delete_permission=False
        )

        # Проверяем обязательные поля
        assert rule.role_id == 1
        assert rule.element_id == 2
        assert rule.id is None  # ID не присвоен до сохранения в БД

        # Проверяем переданные права
        assert rule.read_permission is True
        assert rule.create_permission is False
        assert rule.update_permission is True
        assert rule.delete_permission is False

        # Проверяем права, которые не передавались
        assert rule.read_all_permission is False
        assert rule.update_all_permission is False
        assert rule.delete_all_permission is False

    @pytest.mark.unit
    def test_access_rule_default_permissions(self):
        """Тест: значения по умолчанию для прав"""
        rule = AccessRoleRule(role_id=1, element_id=2)

        assert rule.read_permission is False
        assert rule.read_all_permission is False
        assert rule.create_permission is False
        assert rule.update_permission is False
        assert rule.update_all_permission is False
        assert rule.delete_permission is False
        assert rule.delete_all_permission is False

    @pytest.mark.unit
    def test_access_rule_all_permissions_true(self):
        """Тест: все права включены"""
        rule = AccessRoleRule(
            role_id=1,
            element_id=2,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        )

        assert rule.read_permission is True
        assert rule.read_all_permission is True
        assert rule.create_permission is True
        assert rule.update_permission is True
        assert rule.update_all_permission is True
        assert rule.delete_permission is True
        assert rule.delete_all_permission is True

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_access_rule_to_dict(self):
        """Тест: преобразование в словарь"""
        rule = AccessRoleRule(
            role_id=1,
            element_id=2,
            read_permission=True,
            create_permission=False,
            update_permission=True,
            delete_permission=False
        )

        rule_dict = rule.to_dict()

        # Проверяем поля
        assert rule_dict["id"] is None
        assert rule_dict["role_id"] == 1
        assert rule_dict["element_id"] == 2
        assert rule_dict["read_permission"] is True
        assert rule_dict["read_all_permission"] is False
        assert rule_dict["create_permission"] is False
        assert rule_dict["update_permission"] is True
        assert rule_dict["update_all_permission"] is False
        assert rule_dict["delete_permission"] is False
        assert rule_dict["delete_all_permission"] is False

    @pytest.mark.unit
    def test_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        rule = AccessRoleRule(
            role_id=1,
            element_id=2,
            read_permission=True,
            create_permission=False,
            update_permission=True,
            delete_permission=False,
            created_at=now,
            updated_at=now
        )

        rule_dict = rule.to_dict()

        assert rule_dict["created_at"] == now
        assert rule_dict["updated_at"] == now

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ
    # =========================================================================

    @pytest.mark.unit
    def test_access_rule_repr(self):
        """Тест: строковое представление"""
        rule = AccessRoleRule(
            role_id=1,
            element_id=2,
            read_permission=True,
            create_permission=False,
            update_permission=True,
            delete_permission=False
        )

        repr_str = repr(rule)

        assert "AccessRoleRule" in repr_str
        assert "role_id=1" in repr_str
        assert "element_id=2" in repr_str

    @pytest.mark.unit
    def test_access_rule_repr_with_id(self):
        """Тест: строковое представление с ID"""
        rule = AccessRoleRule(
            id=1,
            role_id=1,
            element_id=2,
            read_permission=True
        )

        repr_str = repr(rule)

        assert "AccessRoleRule" in repr_str
        assert "id=1" in repr_str
        assert "role_id=1" in repr_str
        assert "element_id=2" in repr_str

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_access_rule_relationships(self):
        """Тест: атрибуты отношений"""
        rule = AccessRoleRule()

        assert hasattr(rule, 'role')
        assert hasattr(rule, 'element')
