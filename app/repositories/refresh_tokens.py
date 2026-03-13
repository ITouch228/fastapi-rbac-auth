from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: int, token_jti: str, expires_at: datetime, user_agent: str | None) -> RefreshToken:
        item = RefreshToken(user_id=user_id, token_jti=token_jti, expires_at=expires_at, user_agent=user_agent)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_jti(self, token_jti: str) -> RefreshToken | None:
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_jti == token_jti))
        return result.scalar_one_or_none()

    async def revoke_by_jti(self, token_jti: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_jti == token_jti)
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )
