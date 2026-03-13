"""
Модуль административного API.

Предоставляет эндпоинты для управления RBAC системой:
- Управление ролями (создание, обновление, удаление)
- Управление правилами доступа (просмотр, обновление)
- Управление ролями пользователей (назначение, просмотр)

Все эндпоинты требуют:
- Аутентификации (Bearer token)
- Административных прав (доступ к ресурсу 'rules')
- Rate limiting для защиты от злоупотреблений

Rate limits:
- Создание роли: 10 запросов в минуту
- Назначение роли: 5 запросов в минуту
- Просмотр списков: 20 запросов в минуту
- Обновление правил: 10 запросов в минуту
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models import User
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.schemas.access_rule import AccessRuleResponse, AccessRuleUpdateRequest
from app.schemas.role import (
    AssignRoleRequest,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.access_service import AccessService, Action
from app.services.admin_service import AdminService

router = APIRouter(
    prefix='/admin',
    tags=['admin'],
    responses={
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Доступ запрещён",
            "content": {
                "application/json": {
                    "example": {"detail": "Permission denied"}
                }
            }
        },
        429: {
            "description": "Слишком много запросов",
            "content": {
                "application/json": {
                    "example": {"detail": "Too Many Requests"}
                }
            }
        }
    }
)


# ============================================================================
# Зависимости
# ============================================================================

async def require_admin(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> User:
    """
    Зависимость для проверки прав администратора.

    Проверяет, что текущий пользователь имеет право на чтение ресурса 'rules'.
    Используется во всех эндпоинтах админ-панели.

    **Параметры запроса:**
        - **current_user** (deps): Текущий пользователь из токена
        - **session** (deps): Сессия базы данных

    **Возвращает:**
        User: Пользователь, если права подтверждены

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав (требуется администратор)
    """
    role_repo = RoleRepository(session)
    rule_repo = AccessRuleRepository(session)
    access_service = AccessService(role_repo, rule_repo)
    await access_service.check_access(
        user=current_user,
        element_name='rules',
        action=Action.READ
    )
    return current_user


# ============================================================================
# Эндпоинты для управления ролями
# ============================================================================

@router.post('/roles', response_model=RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
@limiter.limit("10 per minute")
async def create_role(
    request: Request,
    payload: RoleCreateRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Создание новой роли.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Тело запроса:**
        - **name** (str): Уникальное имя роли (только латиница, цифры, подчёркивание)
        - **description** (str, опционально): Описание роли

    **Возвращает:**
        RoleResponse: Созданная роль с ID, именем и описанием

    **Возможные ошибки:**
        - **400**: Роль с таким именем уже существует или невалидные данные
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        POST /api/v1/admin/roles
        {
            "name": "editor",
            "description": "Может редактировать контент"
        }

    **Пример ответа:**
        ```json
        {
            "id": 5,
            "name": "editor",
            "description": "Может редактировать контент"
        }
        ```
    """
    admin_service = AdminService(session)
    return await admin_service.create_role(payload)


@router.get('/roles/{role_name}', response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("20 per minute")
async def get_role(
    request: Request,
    role_name: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Получение роли по имени.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Параметры пути:**
        - **role_name** (str): Имя роли

    **Возвращает:**
        RoleResponse: Роль с ID, именем и описанием

    **Возможные ошибки:**
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        GET /api/v1/admin/roles/editor

    **Пример ответа:**
        ```json
        {
            "id": 5,
            "name": "editor",
            "description": "Может редактировать контент"
        }
        ```
    """
    role_repo = RoleRepository(session)
    return await role_repo.get_by_name(role_name)


@router.patch('/roles/{role_name}', response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("10 per minute")
async def update_role(
    request: Request,
    role_name: str,
    payload: RoleUpdateRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Частичное обновление роли по имени.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Параметры пути:**
        - **role_name** (str): Имя роли

    **Тело запроса:**
        - **name** (str, опционально): Уникальное имя роли (только латиница, цифры, подчёркивание)
        - **description** (str, опционально): Описание роли

    **Возвращает:**
        RoleResponse: Роль с ID, именем и описанием

    **Возможные ошибки:**
        - **404**: Роль не найдена
        - **400**: Роль с таким именем уже существует или невалидные данные
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        PATCH /api/v1/admin/roles/editor
        {
            "name": "new_editor",
            "description": "Может редактировать не весь контент"
        }

    **Пример ответа:**
        ```json
        {
            "id": 5,
            "name": "new_editor",
            "description": "Может редактировать не весь контент"
        }
        ```
    """
    admin_service = AdminService(session)
    return await admin_service.update_role(role_name, payload)


# ============================================================================
# Эндпоинты для управления ролями пользователей
# ============================================================================


@router.get('/users/{user_id}/roles', response_model=list[RoleResponse], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("20 per minute")
async def get_user_roles(request: Request, user_id: int, session: AsyncSession = Depends(get_db)):
    return await AdminService(session).get_user_roles(user_id)


@router.post('/users/{user_id}/roles', response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("5 per minute")
async def assign_role(request: Request, user_id: int, payload: AssignRoleRequest, session: AsyncSession = Depends(get_db)):
    """
    Назначение роли пользователю.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Параметры пути:**
        - **user_id** (int): ID пользователя, которому назначается роль

    **Тело запроса:**
        - **role_name** (str): Имя роли для назначения

    **Возвращает:**
        RoleResponse: Информация о назначенной роли

    **Возможные ошибки:**
        - **404**: Пользователь или роль не найдены
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов (5 в минуту)

    **Пример запроса:**
        POST /api/v1/admin/users/5/roles
        Content-Type: application/json
        {
            "role_name": "manager"
        }

    **Пример ответа:**
        ```json
        {
            "id": 2,
            "name": "manager",
            "description": "Может управлять ресурсами"
        }
        ```
    """
    return await AdminService(session).assign_role(user_id, payload.role_name)


# ============================================================================
# Эндпоинты для управления правилами доступа
# ============================================================================

@router.get('/rules', response_model=list[AccessRuleResponse], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("20 per minute")
async def list_rules(request: Request, session: AsyncSession = Depends(get_db)):
    """
    Получение списка всех правил доступа.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Возвращает:**
        list[AccessRuleResponse]: Список всех правил доступа

    **Возможные ошибки:**
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        GET /api/v1/admin/rules

    **Пример ответа:**
        ```json
        [
            {
                "id": 1,
                "role_id": 1,
                "element_id": 1,
                "read_permission": true,
                "read_all_permission": true,
                "create_permission": false,
                "update_permission": false,
                "update_all_permission": false,
                "delete_permission": false,
                "delete_all_permission": false
            }
        ]
        ```
    """
    return await AdminService(session).list_rules()


@router.patch('/rules/{rule_id}', response_model=AccessRuleResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
@limiter.limit("10 per minute")
async def update_rule(request: Request, rule_id: int, payload: AccessRuleUpdateRequest, session: AsyncSession = Depends(get_db)):
    """
    Частичное обновление правила доступа.

    **Необходимые права:** Административный доступ к ресурсу 'rules'

    **Параметры пути:**
        - **ruld_id** (int) - ID правила доступа

    **Тело запроса:**
        Все поля опциональны. Будут обновлены только переданные поля.

        - **read_permission** (bool, опционально): Право на чтение своих ресурсов
        - **read_all_permission** (bool, опционально): Право на чтение всех ресурсов
        - **create_permission** (bool, опционально): Право на создание
        - **update_permission** (bool, опционально): Право на обновление своих ресурсов
        - **update_all_permission** (bool, опционально): Право на обновление всех ресурсов
        - **delete_permission** (bool, опционально): Право на удаление своих ресурсов
        - **delete_all_permission** (bool, опционально): Право на удаление всех ресурсов

    **Возвращает:**
        AccessRuleResponse: Обновленное правило доступа

    **Возможные ошибки:**
        - **404**: Правило с указанным ID не найдено
        - **403**: Недостаточно прав (требуется администратор)
        - **401**: Пользователь не авторизован
        - **429**: Превышен лимит запросов

    **Пример запроса:**
        PATCH /api/v1/admin/rules/1
        Content-Type: application/json
        {
            "read_permission": true
        }

    **Пример ответа:**
        ```json
        {
            "id": 1,
            "role_id": 1,
            "element_id": 1,
            "read_permission": true,
            "read_all_permission": false,
            "create_permission": true,
            "update_permission": false,
            "update_all_permission": false,
            "delete_permission": false,
            "delete_all_permission": false
        }
        ```
    """
    return await AdminService(session).update_rule(rule_id, payload)
