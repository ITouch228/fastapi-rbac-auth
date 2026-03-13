"""
Модуль mock API ресурсов.

Предоставляет тестовые эндпоинты для проверки RBAC системы:
- Работа с mock продуктами
- Работа с mock заказами
- Работа с mock магазинами

Эндпоинты используются для демонстрации и проверки:
- Чтения списка ресурсов
- Чтения отдельного ресурса
- Создания ресурса
- Обновления ресурса
- Удаления ресурса

Доступ к эндпоинтам определяется через AccessService
и зависит от ролей пользователя и правил доступа
к соответствующему business element.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.models import User
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.schemas.common import APIMessage
from app.services.access_service import AccessService, Action

router = APIRouter(
    tags=['mock-resources'],
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
        }
    }
)

MOCK_DATA = {
    'products': [
        {'id': 1, 'name': 'Phone', 'owner_id': 1},
        {'id': 2, 'name': 'Laptop', 'owner_id': 2},
    ],
    'orders': [
        {'id': 1, 'number': 'ORD-001', 'owner_id': 1},
        {'id': 2, 'number': 'ORD-002', 'owner_id': 2},
    ],
    'shops': [
        {'id': 1, 'name': 'North Shop', 'owner_id': 1},
        {'id': 2, 'name': 'West Shop', 'owner_id': 2},
    ],
}


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def _access_service(session: AsyncSession) -> AccessService:
    """
    Создание сервиса проверки доступа.

    **Параметры:**
        - **session** (AsyncSession): Сессия базы данных

    **Возвращает:**
        AccessService: Сервис проверки прав доступа
    """
    return AccessService(RoleRepository(session), AccessRuleRepository(session))


def _find_item(element: str, item_id: int) -> dict | None:
    """
    Поиск mock объекта по типу ресурса и ID.

    **Параметры:**
        - **element** (str): Название ресурса
        - **item_id** (int): ID объекта

    **Возвращает:**
        dict | None: Найденный объект или None
    """
    return next((item for item in MOCK_DATA[element] if item['id'] == item_id), None)


# ============================================================================
# ЭНДПОИНТЫ ПРОДУКТОВ
# ============================================================================

@router.get('/products')
async def list_products(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение списка mock продуктов.

    **Необходимые права:** Доступ к ресурсу 'products' с действием READ

    **Возвращает:**
        list[dict]: Список mock продуктов

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение продуктов

    **Пример запроса:**
        GET /api/v1/products

    **Пример ответа:**
        ```json
        [
            {
                "id": 1,
                "name": "Phone",
                "owner_id": 1
            },
            {
                "id": 2,
                "name": "Laptop",
                "owner_id": 2
            }
        ]
        ```
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='products',
        action=Action.READ,
        resource_owner_id=current_user.id if current_user else None
    )
    return MOCK_DATA['products']


@router.get('/products/{item_id}')
async def get_product(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение mock продукта по ID.

    **Необходимые права:** Доступ к ресурсу 'products' с действием READ

    **Параметры пути:**
        - **item_id** (int): ID продукта

    **Возвращает:**
        dict | APIMessage: Данные продукта или сообщение, что продукт не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение продукта

    **Пример запроса:**
        GET /api/v1/products/1

    **Пример ответа:**
        ```json
        {
            "id": 1,
            "name": "Phone",
            "owner_id": 1
        }
        ```
    """
    item = _find_item('products', item_id)

    if item is None:
        return APIMessage(message='Mock product not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='products',
        action=Action.READ,
        resource_owner_id=item['owner_id']
    )
    return item


@router.post('/products', status_code=status.HTTP_201_CREATED)
async def create_product(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Создание mock продукта.

    **Необходимые права:** Доступ к ресурсу 'products' с действием CREATE

    **Возвращает:**
        dict: Созданный mock продукт

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на создание продукта

    **Пример запроса:**
        POST /api/v1/products

    **Пример ответа:**
        ```json
        {
            "id": 999,
            "name": "Created mock product",
            "owner_id": 1
        }
        ```
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='products',
        action=Action.CREATE
    )
    return {
        'id': 999,
        'name': 'Created mock product',
        'owner_id': current_user.id if current_user else None
    }


@router.patch('/products/{item_id}')
async def update_product(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Обновление mock продукта.

    **Необходимые права:** Доступ к ресурсу 'products' с действием UPDATE

    **Параметры пути:**
        - **item_id** (int): ID продукта

    **Возвращает:**
        dict | APIMessage: Обновлённый продукт или сообщение, что продукт не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на обновление продукта

    **Пример запроса:**
        PATCH /api/v1/products/1

    **Пример ответа:**
        ```json
        {
            "id": 1,
            "name": "Phone",
            "owner_id": 1,
            "updated": true
        }
        ```
    """
    item = _find_item('products', item_id)

    if item is None:
        return APIMessage(message='Mock product not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='products',
        action=Action.UPDATE,
        resource_owner_id=item['owner_id']
    )
    item['updated'] = True
    return item


@router.delete('/products/{item_id}', response_model=APIMessage)
async def delete_product(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Удаление mock продукта.

    **Необходимые права:** Доступ к ресурсу 'products' с действием DELETE

    **Параметры пути:**
        - **item_id** (int): ID продукта

    **Возвращает:**
        APIMessage: Сообщение об удалении продукта или о том, что продукт не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на удаление продукта

    **Пример запроса:**
        DELETE /api/v1/products/1

    **Пример ответа:**
        ```json
        {
            "message": "Mock product 1 deleted"
        }
        ```
    """
    item = _find_item('products', item_id)

    if item is None:
        return APIMessage(message='Mock product not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='products',
        action=Action.DELETE,
        resource_owner_id=item['owner_id']
    )
    return APIMessage(message=f'Mock product {item_id} deleted')


# ============================================================================
# ЭНДПОИНТЫ ЗАКАЗОВ
# ============================================================================

@router.get('/orders')
async def list_orders(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение списка mock заказов.

    **Необходимые права:** Доступ к ресурсу 'orders' с действием READ

    **Возвращает:**
        list[dict]: Список mock заказов

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение заказов
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='orders',
        action=Action.READ,
        resource_owner_id=current_user.id if current_user else None
    )
    return MOCK_DATA['orders']


@router.get('/orders/{item_id}')
async def get_order(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение mock заказа по ID.

    **Необходимые права:** Доступ к ресурсу 'orders' с действием READ

    **Параметры пути:**
        - **item_id** (int): ID заказа

    **Возвращает:**
        dict | APIMessage: Данные заказа или сообщение, что заказ не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение заказа
    """
    item = _find_item('orders', item_id)

    if item is None:
        return APIMessage(message='Mock order not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='orders',
        action=Action.READ,
        resource_owner_id=item['owner_id']
    )
    return item


@router.post('/orders', status_code=status.HTTP_201_CREATED)
async def create_order(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Создание mock заказа.

    **Необходимые права:** Доступ к ресурсу 'orders' с действием CREATE

    **Возвращает:**
        dict: Созданный mock заказ

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на создание заказа
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='orders',
        action=Action.CREATE
    )
    return {
        'id': 999,
        'number': 'ORD-NEW',
        'owner_id': current_user.id if current_user else None
    }


@router.patch('/orders/{item_id}')
async def update_order(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Обновление mock заказа.

    **Необходимые права:** Доступ к ресурсу 'orders' с действием UPDATE

    **Параметры пути:**
        - **item_id** (int): ID заказа

    **Возвращает:**
        dict | APIMessage: Обновлённый заказ или сообщение, что заказ не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на обновление заказа
    """
    item = _find_item('orders', item_id)

    if item is None:
        return APIMessage(message='Mock order not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='orders',
        action=Action.UPDATE,
        resource_owner_id=item['owner_id']
    )
    item['updated'] = True
    return item


@router.delete('/orders/{item_id}', response_model=APIMessage)
async def delete_order(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Удаление mock заказа.

    **Необходимые права:** Доступ к ресурсу 'orders' с действием DELETE

    **Параметры пути:**
        - **item_id** (int): ID заказа

    **Возвращает:**
        APIMessage: Сообщение об удалении заказа или о том, что заказ не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на удаление заказа
    """
    item = _find_item('orders', item_id)

    if item is None:
        return APIMessage(message='Mock order not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='orders',
        action=Action.DELETE,
        resource_owner_id=item['owner_id']
    )
    return APIMessage(message=f'Mock order {item_id} deleted')


# ============================================================================
# ЭНДПОИНТЫ МАГАЗИНОВ
# ============================================================================

@router.get('/shops')
async def list_shops(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение списка mock магазинов.

    **Необходимые права:** Доступ к ресурсу 'shops' с действием READ

    **Возвращает:**
        list[dict]: Список mock магазинов

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение магазинов
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='shops',
        action=Action.READ,
        resource_owner_id=current_user.id if current_user else None
    )
    return MOCK_DATA['shops']


@router.get('/shops/{item_id}')
async def get_shop(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Получение mock магазина по ID.

    **Необходимые права:** Доступ к ресурсу 'shops' с действием READ

    **Параметры пути:**
        - **item_id** (int): ID магазина

    **Возвращает:**
        dict | APIMessage: Данные магазина или сообщение, что магазин не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на чтение магазина
    """
    item = _find_item('shops', item_id)

    if item is None:
        return APIMessage(message='Mock shop not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='shops',
        action=Action.READ,
        resource_owner_id=item['owner_id']
    )
    return item


@router.post('/shops', status_code=status.HTTP_201_CREATED)
async def create_shop(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Создание mock магазина.

    **Необходимые права:** Доступ к ресурсу 'shops' с действием CREATE

    **Возвращает:**
        dict: Созданный mock магазин

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на создание магазина
    """
    await _access_service(session).check_access(
        user=current_user,
        element_name='shops',
        action=Action.CREATE
    )
    return {
        'id': 999,
        'name': 'New mock shop',
        'owner_id': current_user.id if current_user else None
    }


@router.patch('/shops/{item_id}')
async def update_shop(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Обновление mock магазина.

    **Необходимые права:** Доступ к ресурсу 'shops' с действием UPDATE

    **Параметры пути:**
        - **item_id** (int): ID магазина

    **Возвращает:**
        dict | APIMessage: Обновлённый магазин или сообщение, что магазин не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на обновление магазина
    """
    item = _find_item('shops', item_id)

    if item is None:
        return APIMessage(message='Mock shop not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='shops',
        action=Action.UPDATE,
        resource_owner_id=item['owner_id']
    )
    item['updated'] = True
    return item


@router.delete('/shops/{item_id}', response_model=APIMessage)
async def delete_shop(
    item_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db)
):
    """
    Удаление mock магазина.

    **Необходимые права:** Доступ к ресурсу 'shops' с действием DELETE

    **Параметры пути:**
        - **item_id** (int): ID магазина

    **Возвращает:**
        APIMessage: Сообщение об удалении магазина или о том, что магазин не найден

    **Возможные ошибки:**
        - **401**: Пользователь не авторизован
        - **403**: Недостаточно прав на удаление магазина
    """
    item = _find_item('shops', item_id)

    if item is None:
        return APIMessage(message='Mock shop not found')

    await _access_service(session).check_access(
        user=current_user,
        element_name='shops',
        action=Action.DELETE,
        resource_owner_id=item['owner_id']
    )
    return APIMessage(message=f'Mock shop {item_id} deleted')
