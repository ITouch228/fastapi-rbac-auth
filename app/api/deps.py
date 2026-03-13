from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import unauthorized
from app.core.security import TokenError, decode_token
from app.db.session import get_db
from app.models import User
from app.repositories.users import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except TokenError as exc:
        raise unauthorized(str(exc)) from exc

    if payload.get('type') != 'access':
        raise unauthorized('Expected access token')

    user_id = int(payload.get('sub'))
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


async def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise unauthorized()
    return user
