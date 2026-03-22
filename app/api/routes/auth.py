from fastapi import APIRouter, Depends, Header, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPairResponse
from app.schemas.common import APIMessage
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.core.rate_limiter import limiter

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3 per hour")
async def register(request: Request, payload: RegisterRequest, session: AsyncSession = Depends(get_db)):
    return await AuthService(session).register(payload)


@router.post('/login', response_model=TokenPairResponse)
@limiter.limit("5 per minute")
async def login(
    request: Request,
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    return await AuthService(session).login(payload, user_agent=user_agent)


@router.post('/refresh', response_model=TokenPairResponse)
@limiter.limit("30 per hour")
async def refresh(request: Request, payload: RefreshRequest, session: AsyncSession = Depends(get_db)):
    return await AuthService(session).refresh(payload.refresh_token)


@router.post('/logout', response_model=APIMessage)
@limiter.limit("10 per minute")
async def logout(request: Request, payload: RefreshRequest, session: AsyncSession = Depends(get_db)):
    await AuthService(session).logout(payload.refresh_token)
    return APIMessage(message='Logged out successfully')
