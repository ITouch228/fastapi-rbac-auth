"""
Модуль безопасности приложения.

Содержит:
- Хеширование и проверку паролей
- Создание access token
- Создание refresh token
- Декодирование JWT токенов
- Исключение для ошибок токенов

Используется для:
- Аутентификации пользователей
- Выпуска JWT токенов
- Проверки валидности токенов
- Безопасного хранения паролей
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from jwt import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from app.core.config import get_settings


class TokenError(Exception):
    """
    Исключение для ошибок работы с токенами.

    Возникает при:
    - Истекшем сроке действия токена
    - Невалидной подписи
    - Отсутствии обязательных полей
    - Неверном алгоритме
    - И других ошибках JWT
    """


# =========================================================================
# РАБОТА С ПАРОЛЯМИ
# =========================================================================

def hash_password(password: str) -> str:
    """
    Хеширование пароля.

    Параметры:
        password (str): Пароль в открытом виде

    Возвращает:
        str: Хеш пароля
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Проверка пароля по хешу.

    Параметры:
        password (str): Пароль в открытом виде
        password_hash (str): Сохранённый хеш пароля

    Возвращает:
        bool: True, если пароль совпадает с хешем
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )


# =========================================================================
# СОЗДАНИЕ JWT ТОКЕНОВ
# =========================================================================

def _build_token(
    sub: str,
    token_type: str,
    expires_delta: timedelta
) -> tuple[str, str, datetime]:
    """
    Создание JWT токена.

    Формирует payload токена, создаёт уникальный JTI,
    рассчитывает срок жизни токена и подписывает его.

    Параметры:
        sub (str): Subject токена
        token_type (str): Тип токена
        expires_delta (timedelta): Время жизни токена

    Возвращает:
        tuple[str, str, datetime]:
            - JWT токен
            - JTI токена
            - Время истечения токена
    """
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

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return token, jti, exp


def create_access_token(user_id: int) -> tuple[str, str, datetime]:
    """
    Создание access token.

    Параметры:
        user_id (int): ID пользователя

    Возвращает:
        tuple[str, str, datetime]:
            - Access token
            - JTI токена
            - Время истечения токена
    """
    settings = get_settings()

    return _build_token(
        str(user_id),
        'access',
        timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """
    Создание refresh token.

    Параметры:
        user_id (int): ID пользователя

    Возвращает:
        tuple[str, str, datetime]:
            - Refresh token
            - JTI токена
            - Время истечения токена
    """
    settings = get_settings()

    return _build_token(
        str(user_id),
        'refresh',
        timedelta(days=settings.refresh_token_expire_days)
    )


# =========================================================================
# ДЕКОДИРОВАНИЕ JWT ТОКЕНОВ
# =========================================================================

def decode_token(token: str) -> dict[str, Any]:
    """
    Декодирование JWT токена.

    Проверяет подпись токена, срок его действия и другие параметры.

    Параметры:
        token (str): JWT токен

    Возвращает:
        dict[str, Any]: Payload токена

    Возможные ошибки:
        TokenError: Токен истёк
        TokenError: Токен невалиден
        TokenError: Токен с будущей датой выпуска
        TokenError: Отсутствуют обязательные поля
        TokenError: Неверный алгоритм подписи

    Пример использования:
        try:
            payload = decode_token(token)
            user_id = int(payload['sub'])
        except TokenError as e:
            raise HTTPException(status_code=401, detail=str(e))
    """
    settings = get_settings()

    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                'verify_signature': True,      # Проверка подписи
                'verify_exp': True,            # Проверка срока действия
                'verify_iat': True,            # Проверка времени выпуска
                'verify_nbf': True,            # Проверка времени начала действия
                # Обязательные поля
                'require': ['sub', 'exp', 'iat', 'type', 'jti'],
            }
        )

    except ExpiredSignatureError as exc:
        raise TokenError('Token has expired') from exc

    except ImmatureSignatureError as exc:
        raise TokenError('Token is not yet valid (future iat)') from exc

    except MissingRequiredClaimError as exc:
        raise TokenError(f'Missing required claim: {exc}') from exc

    except InvalidAudienceError as exc:
        raise TokenError('Invalid token audience') from exc

    except InvalidIssuerError as exc:
        raise TokenError('Invalid token issuer') from exc

    except InvalidKeyError as exc:
        raise TokenError('Invalid token key') from exc

    except InvalidAlgorithmError as exc:
        raise TokenError(f'Invalid algorithm: {exc}') from exc

    except InvalidSignatureError as exc:
        raise TokenError('Invalid token signature') from exc

    except InvalidTokenError as exc:
        raise TokenError('Invalid token format') from exc


# =========================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================================

def extract_token_from_header(authorization: str | None) -> str | None:
    """
    Извлекает JWT токен из заголовка Authorization.

    Параметры:
        authorization (str | None): Значение заголовка Authorization

    Возвращает:
        str | None: Токен или None, если заголовок отсутствует или имеет неверный формат

    Пример:
        extract_token_from_header('Bearer eyJhbGci...')
        'eyJhbGci...'
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]


def is_token_expired(payload: dict[str, Any]) -> bool:
    """
    Проверяет, истёк ли срок действия токена.

    Параметры:
        payload (dict[str, Any]): Payload токена

    Возвращает:
        bool: True, если токен истёк
    """
    exp = payload.get('exp')
    if exp is None:
        return True

    now = datetime.now(UTC).timestamp()
    return now > exp
