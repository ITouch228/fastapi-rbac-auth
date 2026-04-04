"""
Integration тесты для административного API.
Описание: проверяют работу административных эндпоинтов,
доступ по ролям, назначение ролей, создание ролей
и обновление правил доступа.
"""

import pytest
from factories import (
    AccessRuleFactory,
    BusinessElementFactory,
    RoleFactory,
    UserFactory,
)
from httpx import AsyncClient


@pytest.mark.integration
class TestAdminAPI:
    """Integration тесты для административного API"""

    # =========================================================================
    # ТЕСТЫ ПОЛУЧЕНИЯ ПРАВИЛ ДОСТУПА
    # =========================================================================

    async def test_list_rules_as_admin(self, client: AsyncClient, admin_headers):
        """Тест: администратор может получить список правил"""
        response = await client.get(
            "/api/v1/admin/rules",
            headers=admin_headers
        )

        # Проверяем статус ответа
        assert response.status_code == 200

        # Проверяем структуру ответа
        data = response.json()
        assert isinstance(data, list)

    async def test_list_rules_as_regular_user(self, client: AsyncClient, auth_headers):
        """Тест: обычный пользователь не может получить список правил"""
        response = await client.get(
            "/api/v1/admin/rules",
            headers=auth_headers
        )

        # Проверяем отказ в доступе
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]

    # =========================================================================
    # ТЕСТЫ ОБНОВЛЕНИЯ ПРАВИЛ ДОСТУПА
    # =========================================================================

    async def test_update_rule_as_admin(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: администратор может обновить правило доступа"""
        RoleFactory._meta.sqlalchemy_session = db_session
        BusinessElementFactory._meta.sqlalchemy_session = db_session
        AccessRuleFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async(name="test_role")
        element = await BusinessElementFactory.create_async(name="test_element")
        rule = await AccessRuleFactory.create_async(
            role_id=role.id,
            element_id=element.id,
            read_permission=False
        )
        await db_session.commit()

        update_data = {
            "read_permission": True,
            "read_all_permission": True,
            "create_permission": False,
            "update_permission": False,
            "update_all_permission": False,
            "delete_permission": False,
            "delete_all_permission": False
        }

        response = await client.patch(
            f"/api/v1/admin/rules/{rule.id}",
            headers=admin_headers,
            json=update_data
        )

        # Проверяем статус ответа
        assert response.status_code == 200

        # Проверяем обновлённые поля
        data = response.json()
        assert data["read_permission"] is True
        assert data["read_all_permission"] is True
        assert data["create_permission"] is False

    async def test_update_rule_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers,
        db_session
    ):
        """Тест: обычный пользователь не может обновить правило доступа"""
        RoleFactory._meta.sqlalchemy_session = db_session
        BusinessElementFactory._meta.sqlalchemy_session = db_session
        AccessRuleFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async()
        element = await BusinessElementFactory.create_async()
        rule = await AccessRuleFactory.create_async(
            role_id=role.id,
            element_id=element.id
        )
        await db_session.commit()

        update_data = {
            "read_permission": True
        }

        response = await client.patch(
            f"/api/v1/admin/rules/{rule.id}",
            headers=auth_headers,
            json=update_data
        )

        # Проверяем отказ в доступе
        assert response.status_code == 403

    # =========================================================================
    # ТЕСТЫ НАЗНАЧЕНИЯ РОЛЕЙ ПОЛЬЗОВАТЕЛЯМ
    # =========================================================================

    async def test_assign_role_as_admin(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: администратор может назначить роль пользователю"""
        UserFactory._meta.sqlalchemy_session = db_session
        RoleFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        role = await RoleFactory.create_async(name="editor")
        await db_session.commit()

        response = await client.post(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers,
            json={"role_name": role.name}
        )

        # Проверяем успешное назначение роли
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == role.name

        # Проверяем, что роль действительно появилась у пользователя
        roles_response = await client.get(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers
        )

        assert roles_response.status_code == 200
        roles_data = roles_response.json()
        assert any(role_data["name"] == role.name for role_data in roles_data)

    async def test_assign_role_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers,
        db_session
    ):
        """Тест: обычный пользователь не может назначить роль"""
        UserFactory._meta.sqlalchemy_session = db_session
        RoleFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        role = await RoleFactory.create_async()
        await db_session.commit()

        response = await client.post(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=auth_headers,
            json={"role_name": role.name}
        )

        # Проверяем отказ в доступе
        assert response.status_code == 403

    async def test_assign_role_to_nonexistent_user(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: назначение роли несуществующему пользователю возвращает 404"""
        RoleFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async()
        await db_session.commit()

        response = await client.post(
            "/api/v1/admin/users/99999/roles",
            headers=admin_headers,
            json={"role_name": role.name}
        )

        # Проверяем ошибку отсутствующего пользователя
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    async def test_assign_nonexistent_role(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: назначение несуществующей роли возвращает 404"""
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        await db_session.commit()

        response = await client.post(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers,
            json={"role_name": "nonexistent_role"}
        )

        # Проверяем ошибку отсутствующей роли
        assert response.status_code == 404
        assert "Role not found" in response.json()["detail"]

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ РОЛЕЙ
    # =========================================================================

    async def test_create_role_as_admin(
        self,
        client: AsyncClient,
        admin_headers
    ):
        """Тест: администратор может создать новую роль"""
        create_data = {
            "name": "moderator",
            "description": "Moderator role with limited permissions"
        }

        response = await client.post(
            "/api/v1/admin/roles",
            headers=admin_headers,
            json=create_data
        )

        # Проверяем успешное создание роли
        assert response.status_code == 201

        # Проверяем поля созданной роли
        data = response.json()
        assert data["name"] == "moderator"
        assert data["description"] == "Moderator role with limited permissions"

    async def test_create_role_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Тест: обычный пользователь не может создать роль"""
        create_data = {
            "name": "moderator",
            "description": "Moderator role with limited permissions"
        }

        response = await client.post(
            "/api/v1/admin/roles",
            headers=auth_headers,
            json=create_data
        )

        # Проверяем отказ в доступе
        assert response.status_code == 403

    async def test_create_duplicate_role(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: создание роли с существующим именем возвращает 400"""
        RoleFactory._meta.sqlalchemy_session = db_session

        await RoleFactory.create_async(name="moderator")
        await db_session.commit()

        create_data = {
            "name": "moderator",
            "description": "Another moderator role"
        }

        response = await client.post(
            "/api/v1/admin/roles",
            headers=admin_headers,
            json=create_data
        )

        # Проверяем ошибку дублирования роли
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    # =========================================================================
    # ТЕСТЫ ПОЛУЧЕНИЯ РОЛЕЙ ПОЛЬЗОВАТЕЛЯ
    # =========================================================================

    async def test_get_user_roles_as_admin(
        self,
        client: AsyncClient,
        admin_headers,
        db_session
    ):
        """Тест: администратор может получить список ролей пользователя"""
        UserFactory._meta.sqlalchemy_session = db_session
        RoleFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        await RoleFactory.create_async(name="role1")
        await RoleFactory.create_async(name="role2")
        await db_session.commit()

        await client.post(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers,
            json={"role_name": "role1"}
        )
        await client.post(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers,
            json={"role_name": "role2"}
        )

        response = await client.get(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=admin_headers
        )

        # Проверяем успешное получение ролей
        assert response.status_code == 200

        # Проверяем состав ролей
        data = response.json()
        assert len(data) == 2
        assert {role["name"] for role in data} == {"role1", "role2"}

    async def test_get_user_roles_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers,
        db_session
    ):
        """Тест: обычный пользователь не может получить роли другого пользователя"""
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        await db_session.commit()

        response = await client.get(
            f"/api/v1/admin/users/{user.id}/roles",
            headers=auth_headers
        )

        # Проверяем отказ в доступе
        assert response.status_code == 403

    async def test_get_user_roles_nonexistent_user(
        self,
        client: AsyncClient,
        admin_headers
    ):
        """Тест: получение ролей несуществующего пользователя возвращает 404"""
        response = await client.get(
            "/api/v1/admin/users/99999/roles",
            headers=admin_headers
        )

        # Проверяем ошибку отсутствующего пользователя
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
