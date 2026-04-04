import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Role, BusinessElement, AccessRoleRule, UserRole
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.services.access_service import AccessService, Action
from tests.factories import UserFactory, RoleFactory, BusinessElementFactory


@pytest.mark.asyncio
async def test_access_service_full_integration(db_session: AsyncSession):
    """Полная интеграция AccessService с репозиториями и моделями"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session

    # Создание тестовых данных
    user = await UserFactory.create_async(full_name="Test User", email="test@example.com")
    role = await RoleFactory.create_async(name="test_role", description="Test role")
    element = await BusinessElementFactory.create_async(name="documents", description="Document management")

    # Назначение роли пользователю
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.flush()

    # Создание правила доступа
    rule = AccessRoleRule(
        role_id=role.id,
        element_id=element.id,
        read_permission=True,
        read_all_permission=False,
        create_permission=True,
        update_permission=False,
        update_all_permission=False,
        delete_permission=False,
        delete_all_permission=False
    )
    db_session.add(rule)
    await db_session.flush()

    # Создание сервиса с репозиториями
    role_repo = RoleRepository(db_session)
    rule_repo = AccessRuleRepository(db_session)
    access_service = AccessService(role_repo, rule_repo)

    # Тестирование доступа к своим ресурсам (должно пройти)
    await access_service.check_access(
        user=user,
        element_name="documents",
        action=Action.READ,
        resource_owner_id=user.id
    )

    # Тестирование создания (должно пройти)
    await access_service.check_access(
        user=user,
        element_name="documents",
        action=Action.CREATE
    )

    # Тестирование доступа к чужим ресурсам (должно быть запрещено)
    with pytest.raises(Exception):  # forbidden exception
        await access_service.check_access(
            user=user,
            element_name="documents",
            action=Action.UPDATE,
            resource_owner_id=999  # другой пользователь
        )

    # Тестирование доступа без ролей (должно быть запрещено)
    user_without_roles = await UserFactory.create_async(
        full_name="No Role User",
        email="no-role@example.com"
    )
    with pytest.raises(Exception):  # forbidden exception
        await access_service.check_access(
            user=user_without_roles,
            element_name="documents",
            action=Action.READ
        )

    # Тестирование неактивного пользователя (должно быть запрещено)
    inactive_user = await UserFactory.create_async(
        full_name="Inactive User",
        email="inactive@example.com",
        is_active=False
    )
    with pytest.raises(Exception):  # unauthorized exception
        await access_service.check_access(
            user=inactive_user,
            element_name="documents",
            action=Action.READ
        )


@pytest.mark.asyncio
async def test_access_service_different_permissions(db_session: AsyncSession):
    """Тестирование различных комбинаций прав доступа"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session

    # Создание тестовых данных
    user = await UserFactory.create_async(full_name="Test User", email="test@example.com")
    role = await RoleFactory.create_async(name="limited_role", description="Limited access role")
    element = await BusinessElementFactory.create_async(name="reports", description="Report management")

    # Назначение роли пользователю
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.flush()

    # Создание правила с правами на все ресурсы (all_permission)
    all_access_rule = AccessRoleRule(
        role_id=role.id,
        element_id=element.id,
        read_permission=False,
        read_all_permission=True,  # Может читать все
        create_permission=False,
        update_permission=False,
        update_all_permission=True,  # Может обновлять все
        delete_permission=False,
        delete_all_permission=False
    )
    db_session.add(all_access_rule)
    await db_session.flush()

    # Создание сервиса
    role_repo = RoleRepository(db_session)
    rule_repo = AccessRuleRepository(db_session)
    access_service = AccessService(role_repo, rule_repo)

    # Тестирование прав на чтение всех ресурсов (должно пройти)
    await access_service.check_access(
        user=user,
        element_name="reports",
        action=Action.READ,
        resource_owner_id=999  # чужой ресурс
    )

    # Тестирование прав на обновление всех ресурсов (должно пройти)
    await access_service.check_access(
        user=user,
        element_name="reports",
        action=Action.UPDATE,
        resource_owner_id=999  # чужой ресурс
    )

    # Тестирование прав на удаление (должно быть запрещено)
    with pytest.raises(Exception):  # forbidden exception
        await access_service.check_access(
            user=user,
            element_name="reports",
            action=Action.DELETE,
            resource_owner_id=999  # чужой ресурс
        )

    # Тестирование прав на создание (должно быть запрещено)
    with pytest.raises(Exception):  # forbidden exception
        await access_service.check_access(
            user=user,
            element_name="reports",
            action=Action.CREATE
        )


@pytest.mark.asyncio
async def test_access_service_multiple_roles(db_session: AsyncSession):
    """Тестирование AccessService с несколькими ролями у пользователя"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session

    # Создание тестовых данных
    user = await UserFactory.create_async(full_name="Multi Role User", email="multi@example.com")
    role1 = await RoleFactory.create_async(name="role1", description="First role")
    role2 = await RoleFactory.create_async(name="role2", description="Second role")
    element = await BusinessElementFactory.create_async(name="projects", description="Project management")

    # Назначение нескольких ролей пользователю
    db_session.add_all([
        UserRole(user_id=user.id, role_id=role1.id),
        UserRole(user_id=user.id, role_id=role2.id)
    ])
    await db_session.flush()

    # Создание правил для разных ролей
    rule1 = AccessRoleRule(
        role_id=role1.id,
        element_id=element.id,
        read_permission=True,  # Может читать свои
        read_all_permission=False,
        create_permission=False,
        update_permission=False,
        update_all_permission=False,
        delete_permission=False,
        delete_all_permission=False
    )
    rule2 = AccessRoleRule(
        role_id=role2.id,
        element_id=element.id,
        read_permission=False,
        read_all_permission=True,  # Может читать все
        create_permission=False,
        update_permission=False,
        update_all_permission=False,
        delete_permission=False,
        delete_all_permission=False
    )
    db_session.add_all([rule1, rule2])
    await db_session.flush()

    # Создание сервиса
    role_repo = RoleRepository(db_session)
    rule_repo = AccessRuleRepository(db_session)
    access_service = AccessService(role_repo, rule_repo)

    # Тестирование доступа через первую роль (чтение своих)
    await access_service.check_access(
        user=user,
        element_name="projects",
        action=Action.READ,
        resource_owner_id=user.id
    )

    # Тестирование доступа через вторую роль (чтение всех)
    await access_service.check_access(
        user=user,
        element_name="projects",
        action=Action.READ,
        resource_owner_id=999  # чужой ресурс
    )
