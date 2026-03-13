from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings


class TokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def _build_token(sub: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    settings = get_settings()
    now = datetime.now(UTC)
    exp = now + expires_delta
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        'sub': sub,
        'type': token_type,
        'jti': jti,
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key,
                       algorithm=settings.jwt_algorithm)
    return token, jti, exp


def create_access_token(user_id: int) -> tuple[str, str, datetime]:
    settings = get_settings()
    return _build_token(str(user_id), 'access', timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    settings = get_settings()
    return _build_token(str(user_id), 'refresh', timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise TokenError('Token expired') from exc
    except InvalidTokenError as exc:
        raise TokenError('Invalid token') from exc
