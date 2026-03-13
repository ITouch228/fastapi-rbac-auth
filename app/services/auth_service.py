from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, unauthorized
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    async def register(self, payload: RegisterRequest) -> User:
        if payload.password != payload.password_repeat:
            raise bad_request('Passwords do not match')

        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise bad_request('Email already registered')

        user = await self.user_repo.create(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        user_role = await self.role_repo.get_by_name('user')
        if user_role is None:
            raise bad_request('Base role user not found in database')
        await self.role_repo.assign_single_role(user.id, user_role.id)
        await self.session.commit()
        return user

    async def login(self, payload: LoginRequest, *, user_agent: str | None = None) -> dict[str, str]:
        user = await self.user_repo.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise unauthorized('Invalid email or password')
        if not user.is_active:
            raise unauthorized('User is inactive')

        access_token, _, _ = create_access_token(user.id)
        refresh_token, refresh_jti, refresh_exp = create_refresh_token(user.id)
        await self.refresh_repo.create(user_id=user.id, token_jti=refresh_jti, expires_at=refresh_exp, user_agent=user_agent)
        await self.session.commit()
        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        payload = decode_token(refresh_token)
        if payload.get('type') != 'refresh':
            raise unauthorized('Expected refresh token')

        jti = payload.get('jti')
        user_id = int(payload.get('sub'))
        stored = await self.refresh_repo.get_by_jti(jti)
        if stored is None or stored.is_revoked:
            raise unauthorized('Refresh token is revoked or not found')

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise unauthorized('User is inactive')

        access_token, _, _ = create_access_token(user.id)
        await self.session.commit()
        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}

    async def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload.get('type') != 'refresh':
            raise unauthorized('Expected refresh token')
        await self.refresh_repo.revoke_by_jti(payload['jti'])
        await self.session.commit()
