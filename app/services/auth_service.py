"""
Сервис аутентификации пользователей.

Содержит бизнес-логику для:
- Регистрации пользователя
- Входа в систему
- Обновления access token по refresh token
- Выхода из системы

Используется для:
- Создания новых пользователей
- Проверки учётных данных
- Выдачи JWT токенов
- Управления refresh token
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Сервис аутентификации пользователей"""

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация сервиса аутентификации.

        **Параметры:**
            - **session** (AsyncSession): Сессия базы данных
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    # =========================================================================
    # МЕТОДЫ РЕГИСТРАЦИИ
    # =========================================================================

    async def register(self, payload: RegisterRequest) -> User:
        """
        Регистрация нового пользователя.

        Проверяет, что пользователь с таким email ещё не существует,
        создаёт нового пользователя, хеширует пароль
        и назначает базовую роль `user`.

        **Параметры:**
            - **payload** (RegisterRequest): Данные регистрации

        **Возвращает:**
            User: Созданный пользователь

        **Возможные ошибки:**
            - **400**: Email уже зарегистрирован
            - **400**: Базовая роль user отсутствует в базе данных
        """
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

        await self.role_repo.assign_role(user.id, user_role.id)
        await self.session.commit()

        return user

    # =========================================================================
    # МЕТОДЫ ВХОДА В СИСТЕМУ
    # =========================================================================

    async def login(
        self,
        payload: LoginRequest,
        *,
        user_agent: str | None = None
    ) -> dict[str, str]:
        """
        Вход пользователя в систему.

        Проверяет email и пароль пользователя,
        создаёт access token и refresh token,
        сохраняет refresh token в базе данных.

        **Параметры:**
            - **payload** (LoginRequest): Данные для входа
            - **user_agent** (str | None): User-Agent клиента

        **Возвращает:**
            dict[str, str]: Access token, refresh token и тип токена

        **Возможные ошибки:**
            - **401**: Неверный email или пароль
            - **401**: Пользователь неактивен
        """
        user = await self.user_repo.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.password_hash):
            raise unauthorized('Invalid email or password')

        if not user.is_active:
            raise unauthorized('User is inactive')

        access_token, _, _ = create_access_token(user.id)
        refresh_token, refresh_jti, refresh_exp = create_refresh_token(user.id)

        await self.refresh_repo.create(
            user_id=user.id,
            token_jti=refresh_jti,
            expires_at=refresh_exp,
            user_agent=user_agent
        )
        await self.session.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    # =========================================================================
    # МЕТОДЫ ОБНОВЛЕНИЯ ТОКЕНОВ
    # =========================================================================

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        """
        Обновление access token по refresh token.

        Проверяет тип токена, ищет refresh token в базе,
        проверяет пользователя и создаёт новый access token.

        **Параметры:**
            - **refresh_token** (str): Refresh token

        **Возвращает:**
            dict[str, str]: Новый access token, исходный refresh token и тип токена

        **Возможные ошибки:**
            - **401**: Ожидался refresh token
            - **401**: Refresh token отозван или не найден
            - **401**: Пользователь неактивен
        """
        payload = decode_token(refresh_token)

        if payload.get('type') != 'refresh':
            raise unauthorized('Expected refresh token')

        sub = payload.get('sub')
        jti = payload.get('jti')

        if not sub or not jti:
            raise unauthorized('Invalid token payload')

        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise unauthorized('Invalid token payload')

        stored = await self.refresh_repo.get_by_jti(jti)

        if stored is None or stored.is_revoked:
            raise unauthorized('Refresh token is revoked or not found')

        if stored.user_id != user_id:
            raise unauthorized('Invalid token payload')

        user = await self.user_repo.get_by_id(user_id)

        if user is None or not user.is_active:
            raise unauthorized('User is inactive')

        access_token, _, _ = create_access_token(user.id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    # =========================================================================
    # МЕТОДЫ ВЫХОДА ИЗ СИСТЕМЫ
    # =========================================================================

    async def logout(self, refresh_token: str) -> None:
        """
        Выход пользователя из системы.

        Проверяет тип токена и отзывает refresh token
        по его JTI.

        **Параметры:**
            - **refresh_token** (str): Refresh token для отзыва

        **Возможные ошибки:**
            - **401**: Ожидался refresh token
        """
        payload = decode_token(refresh_token)

        if payload.get('type') != 'refresh':
            raise unauthorized('Expected refresh token')

        await self.refresh_repo.revoke_by_jti(payload['jti'])
        await self.session.commit()
