from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.models import User
from app.schemas.common import APIMessage
from app.services.access_service import AccessService, Action
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository
from app.core.rate_limiter import limiter

router = APIRouter(tags=['mock-resources'])

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


def _access_service(session: AsyncSession) -> AccessService:
    return AccessService(RoleRepository(session), AccessRuleRepository(session))


def _find_item(element: str, item_id: int) -> dict | None:
    return next((item for item in MOCK_DATA[element] if item['id'] == item_id), None)


@router.get('/products')
async def list_products(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='products', action=Action.READ, resource_owner_id=current_user.id if current_user else None)
    return MOCK_DATA['products']


@router.get('/products/{item_id}')
async def get_product(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('products', item_id)
    if item is None:
        return APIMessage(message='Mock product not found')
    await _access_service(session).check_access(user=current_user, element_name='products', action=Action.READ, resource_owner_id=item['owner_id'])
    return item


@router.post('/products', status_code=status.HTTP_201_CREATED)
async def create_product(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='products', action=Action.CREATE)
    return {'id': 999, 'name': 'Created mock product', 'owner_id': current_user.id if current_user else None}


@router.patch('/products/{item_id}')
async def update_product(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('products', item_id)
    if item is None:
        return APIMessage(message='Mock product not found')
    await _access_service(session).check_access(user=current_user, element_name='products', action=Action.UPDATE, resource_owner_id=item['owner_id'])
    item['updated'] = True
    return item


@router.delete('/products/{item_id}', response_model=APIMessage)
async def delete_product(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('products', item_id)
    if item is None:
        return APIMessage(message='Mock product not found')
    await _access_service(session).check_access(user=current_user, element_name='products', action=Action.DELETE, resource_owner_id=item['owner_id'])
    return APIMessage(message=f'Mock product {item_id} deleted')


@router.get('/orders')
async def list_orders(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='orders', action=Action.READ, resource_owner_id=current_user.id if current_user else None)
    return MOCK_DATA['orders']


@router.get('/orders/{item_id}')
async def get_order(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('orders', item_id)
    if item is None:
        return APIMessage(message='Mock order not found')
    await _access_service(session).check_access(user=current_user, element_name='orders', action=Action.READ, resource_owner_id=item['owner_id'])
    return item


@router.post('/orders', status_code=status.HTTP_201_CREATED)
async def create_order(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='orders', action=Action.CREATE)
    return {'id': 999, 'number': 'ORD-NEW', 'owner_id': current_user.id if current_user else None}


@router.patch('/orders/{item_id}')
async def update_order(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('orders', item_id)
    if item is None:
        return APIMessage(message='Mock order not found')
    await _access_service(session).check_access(user=current_user, element_name='orders', action=Action.UPDATE, resource_owner_id=item['owner_id'])
    item['updated'] = True
    return item


@router.delete('/orders/{item_id}', response_model=APIMessage)
async def delete_order(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('orders', item_id)
    if item is None:
        return APIMessage(message='Mock order not found')
    await _access_service(session).check_access(user=current_user, element_name='orders', action=Action.DELETE, resource_owner_id=item['owner_id'])
    return APIMessage(message=f'Mock order {item_id} deleted')


@router.get('/shops')
async def list_shops(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='shops', action=Action.READ, resource_owner_id=current_user.id if current_user else None)
    return MOCK_DATA['shops']


@router.get('/shops/{item_id}')
async def get_shop(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('shops', item_id)
    if item is None:
        return APIMessage(message='Mock shop not found')
    await _access_service(session).check_access(user=current_user, element_name='shops', action=Action.READ, resource_owner_id=item['owner_id'])
    return item


@router.post('/shops', status_code=status.HTTP_201_CREATED)
async def create_shop(current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    await _access_service(session).check_access(user=current_user, element_name='shops', action=Action.CREATE)
    return {'id': 999, 'name': 'New mock shop', 'owner_id': current_user.id if current_user else None}


@router.patch('/shops/{item_id}')
async def update_shop(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('shops', item_id)
    if item is None:
        return APIMessage(message='Mock shop not found')
    await _access_service(session).check_access(user=current_user, element_name='shops', action=Action.UPDATE, resource_owner_id=item['owner_id'])
    item['updated'] = True
    return item


@router.delete('/shops/{item_id}', response_model=APIMessage)
async def delete_shop(item_id: int, current_user: User | None = Depends(get_current_user_optional), session: AsyncSession = Depends(get_db)):
    item = _find_item('shops', item_id)
    if item is None:
        return APIMessage(message='Mock shop not found')
    await _access_service(session).check_access(user=current_user, element_name='shops', action=Action.DELETE, resource_owner_id=item['owner_id'])
    return APIMessage(message=f'Mock shop {item_id} deleted')
