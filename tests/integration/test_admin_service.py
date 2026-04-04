import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import bad_request, not_found
from app.models import User, Role, BusinessElement, AccessRoleRule, UserRole
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.services.admin_service import AdminService
from app.schemas.access_rule import AccessRuleUpdateRequest
from app.schemas.role import RoleCreateRequest, RoleUpdateRequest
from tests.factories import UserFactory, RoleFactory, BusinessElementFactory


@pytest.mark.asyncio
async def test_admin_service_full_integration(db_session: AsyncSession):
    """Полная интеграция AdminService с репозиториями и моделями"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session

    # Создание сервиса
    admin_service = AdminService(db_session)

    # Тестирование создания роли
    create_payload = RoleCreateRequest(
        name="test_role", description="Test role description")
    created_role = await admin_service.create_role(create_payload)

    assert created_role.name == "test_role"
    assert created_role.description == "Test role description"
    assert created_role.id is not None

    # Попытка создать роль с тем же именем (должна быть ошибка)
    duplicate_payload = RoleCreateRequest(
        name="test_role", description="Another description")
    with pytest.raises(Exception):  # bad_request exception
        await admin_service.create_role(duplicate_payload)

    # Тестирование обновления роли
    update_payload = RoleUpdateRequest(
        name="updated_role", description="Updated description")
    updated_role = await admin_service.update_role("test_role", update_payload)

    assert updated_role.name == "updated_role"
    assert updated_role.description == "Updated description"

    # Тестирование получения несуществующей роли (должна быть ошибка)
    with pytest.raises(Exception):  # not_found exception
        await admin_service.update_role("nonexistent_role", update_payload)

    # Создание пользователя для тестирования назначения ролей
    user = await UserFactory.create_async(full_name="Test User", email="test@example.com")
    await db_session.refresh(user)

    # Тестирование назначения роли пользователю
    assigned_role = await admin_service.assign_role(user.id, "updated_role")
    assert assigned_role.name == "updated_role"

    # Проверка получения ролей пользователя
    user_roles = await admin_service.get_user_roles(user.id)
    assert len(user_roles) == 1
    assert user_roles[0].name == "updated_role"

    # Тестирование получения ролей несуществующего пользователя
    # В репозитории метод get_user_roles не проверяет существование пользователя,
    # а просто возвращает пустой список, если у пользователя нет ролей
    user_roles = await admin_service.get_user_roles(999999)
    assert len(user_roles) == 0


@pytest.mark.asyncio
async def test_admin_service_rule_management(db_session: AsyncSession):
    """Тестирование управления правилами доступа через AdminService"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session

    # Создание тестовых данных
    user = await UserFactory.create_async(full_name="Test User", email="test@example.com")
    role = await RoleFactory.create_async(name="test_role", description="Test role")
    element = await BusinessElementFactory.create_async(name="documents", description="Documents")

    # Создание правила доступа напрямую в базе
    rule = AccessRoleRule(
        role_id=role.id,
        element_id=element.id,
        read_permission=True,
        read_all_permission=False,
        create_permission=False,
        update_permission=False,
        update_all_permission=False,
        delete_permission=False,
        delete_all_permission=False
    )
    db_session.add(rule)
    await db_session.flush()
    await db_session.refresh(rule)

    # Создание сервиса
    admin_service = AdminService(db_session)

    # Тестирование получения списка правил
    rules = await admin_service.list_rules()
    assert len(rules) >= 1
    rule_in_list = next((r for r in rules if r.id == rule.id), None)
    assert rule_in_list is not None
    assert rule_in_list.read_permission is True

    # Тестирование обновления правила
    update_payload = AccessRuleUpdateRequest(
        read_permission=False,
        read_all_permission=True,
        create_permission=True
    )
    updated_rule = await admin_service.update_rule(rule.id, update_payload)

    assert updated_rule.id == rule.id
    assert updated_rule.read_permission is False
    assert updated_rule.read_all_permission is True
    assert updated_rule.create_permission is True

    # Тестирование обновления несуществующего правила
    with pytest.raises(Exception):  # not_found exception
        await admin_service.update_rule(999999, update_payload)


@pytest.mark.asyncio
async def test_admin_service_edge_cases(db_session: AsyncSession):
    """Тестирование крайних случаев и граничных условий в AdminService"""
    # Подготовка фабрик
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

    # Создание сервиса
    admin_service = AdminService(db_session)

    # Тестирование обновления роли с изменением имени на существующее
    role1_payload = RoleCreateRequest(
        name="first_role", description="First role")
    role2_payload = RoleCreateRequest(
        name="second_role", description="Second role")

    await admin_service.create_role(role1_payload)
    await admin_service.create_role(role2_payload)

    # Попытка переименовать role2 в имя role1 (должна быть ошибка)
    update_payload = RoleUpdateRequest(name="first_role")  # уже существует
    with pytest.raises(Exception):  # bad_request exception
        await admin_service.update_role("second_role", update_payload)

    # Тестирование назначения несуществующей роли пользователю
    user = await UserFactory.create_async(full_name="Test User", email="test@example.com")
    await db_session.refresh(user)

    with pytest.raises(Exception):  # not_found exception
        await admin_service.assign_role(user.id, "nonexistent_role")

    # Тестирование назначения роли несуществующему пользователю
    with pytest.raises(Exception):  # not_found exception
        await admin_service.assign_role(999999, "first_role")

    # Тестирование обновления с None значениями (exclude_none)
    none_payload = RoleUpdateRequest(
        description=None)  # не должно изменить имя
    updated_role = await admin_service.update_role("first_role", none_payload)
    assert updated_role.name == "first_role"  # имя не должно измениться
    # описание не должно измениться, т.к. None исключается из обновления
