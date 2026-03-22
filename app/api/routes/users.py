from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import APIMessage
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService
from app.core.rate_limiter import limiter

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserResponse)
@limiter.limit("60 per minute")
async def get_me(request: Request, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await UserService(session).get_current(current_user)


@router.patch('/me', response_model=UserResponse)
@limiter.limit("5 per minute")
async def update_me(
    request: Request,
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await UserService(session).update_me(current_user, payload)


@router.delete('/me', response_model=APIMessage)
@limiter.limit("1 per day")
async def delete_me(request: Request, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await UserService(session).soft_delete_me(current_user)
    return APIMessage(message='User soft-deleted and logged out')
