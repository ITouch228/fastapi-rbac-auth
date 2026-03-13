from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, unauthorized
from app.models import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.user import UserUpdateRequest


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    async def get_current(self, user: User | None) -> User:
        if user is None or not user.is_active:
            raise unauthorized()
        return user

    async def update_me(self, user: User | None, payload: UserUpdateRequest) -> User:
        if user is None or not user.is_active:
            raise unauthorized()
        if payload.email and payload.email != user.email:
            existing = await self.user_repo.get_by_email(payload.email)
            if existing and existing.id != user.id:
                raise bad_request('Email already registered')
        updated = await self.user_repo.update_profile(user, full_name=payload.full_name, email=payload.email)
        await self.session.commit()
        return updated

    async def soft_delete_me(self, user: User | None) -> None:
        if user is None or not user.is_active:
            raise unauthorized()
        await self.user_repo.soft_delete(user)
        await self.refresh_repo.revoke_all_for_user(user.id)
        await self.session.commit()
