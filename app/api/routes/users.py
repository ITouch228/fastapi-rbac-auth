from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import APIMessage
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await UserService(session).get_current(current_user)


@router.patch('/me', response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await UserService(session).update_me(current_user, payload)


@router.delete('/me', response_model=APIMessage)
async def delete_me(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await UserService(session).soft_delete_me(current_user)
    return APIMessage(message='User soft-deleted and logged out')
