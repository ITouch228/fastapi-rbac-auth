"""
Unit тесты для AuthService.

Тестируют бизнес-логику аутентификации в изоляции от реальных зависимостей.
Все внешние зависимости (репозитории, БД) заменены на моки.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


class TestAuthService:
    """Unit тесты для AuthService с моками"""

    @pytest.fixture
    def mock_session(self):
        """Мок сессии базы данных"""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def auth_service(self, mock_session):
        """Создание AuthService с моками"""
        service = AuthService(mock_session)
        # Мокаем репозитории
        service.user_repo = AsyncMock()
        service.role_repo = AsyncMock()
        service.refresh_repo = AsyncMock()
        return service

    @pytest.fixture
    def sample_user(self):
        """Создание тестового пользователя"""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash=hash_password("Test123!@#"),
            is_active=True
        )

    @pytest.fixture
    def sample_user_role(self):
        """Создание тестовой роли user"""
        return Role(
            id=1,
            name="user",
            description="Regular user role"
        )

    @pytest.fixture
    def sample_refresh_token(self):
        """Создание тестового refresh токена"""
        return RefreshToken(
            id=1,
            user_id=1,
            token_jti="test-jti-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
            user_agent="test-agent"
        )

    @pytest.fixture
    def valid_register_payload(self):
        """Валидные данные для регистрации"""
        return RegisterRequest(
            full_name="Test User",
            email="test@example.com",
            password="Test123!@#",
            password_repeat="Test123!@#"
        )

    @pytest.fixture
    def valid_login_payload(self):
        """Валидные данные для логина"""
        return LoginRequest(
            email="test@example.com",
            password="Test123!@#"
        )

    # ============================================================================
    # Тесты для register
    # ============================================================================

    @pytest.mark.asyncio
    async def test_register_success(
        self, auth_service, mock_session, valid_register_payload, sample_user, sample_user_role
    ):
        """
        Тест успешной регистрации пользователя.

        Проверяет:
        - Проверка совпадения паролей
        - Проверка уникальности email
        - Создание пользователя
        - Назначение роли 'user'
        - Коммит и возврат пользователя
        """
        # Arrange
        auth_service.user_repo.get_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create = AsyncMock(return_value=sample_user)
        auth_service.role_repo.get_by_name = AsyncMock(
            return_value=sample_user_role)
        auth_service.role_repo.assign_role = AsyncMock()

        # Act
        result = await auth_service.register(valid_register_payload)

        # Assert
        # Проверяем проверку email
        auth_service.user_repo.get_by_email.assert_called_once_with(
            "test@example.com")

        # Проверяем создание пользователя
        auth_service.user_repo.create.assert_called_once()
        created_user = auth_service.user_repo.create.call_args[1]
        assert created_user["full_name"] == "Test User"
        assert created_user["email"] == "test@example.com"
        assert created_user["password_hash"] is not None

        # Проверяем назначение роли
        auth_service.role_repo.get_by_name.assert_called_once_with("user")
        auth_service.role_repo.assign_role.assert_called_once_with(1, 1)

        # Проверяем коммит
        mock_session.commit.assert_called_once()

        # Проверяем результат
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, valid_register_payload, sample_user):
        """
        Тест регистрации с уже существующим email.

        Ожидаемый результат: HTTPException 400
        """
        # Arrange
        auth_service.user_repo.get_by_email = AsyncMock(
            return_value=sample_user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(valid_register_payload)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

        # Проверяем, что создание не вызывалось
        auth_service.user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_role_not_found(
        self, auth_service, mock_session, valid_register_payload, sample_user
    ):
        """
        Тест регистрации, когда роль 'user' не найдена в БД.

        Ожидаемый результат: HTTPException 400
        """
        # Arrange
        auth_service.user_repo.get_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create = AsyncMock(return_value=sample_user)
        auth_service.role_repo.get_by_name = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(valid_register_payload)

        assert exc_info.value.status_code == 400
        assert "Base role user not found" in str(exc_info.value.detail)

        # Проверяем, что роль не назначалась
        auth_service.role_repo.assign_role.assert_not_called()


# ============================================================================
# Тесты для login
# ============================================================================

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_session, valid_login_payload, sample_user):
        """
        Тест успешного входа.

        Проверяет:
        - Поиск пользователя по email
        - Проверка пароля
        - Проверка активности пользователя
        - Создание токенов
        - Создание refresh токена в БД
        """
        # Arrange
        auth_service.user_repo.get_by_email = AsyncMock(
            return_value=sample_user)
        auth_service.refresh_repo.create = AsyncMock()

        # Act
        result = await auth_service.login(valid_login_payload, user_agent="test-agent")

        # Assert
        # Проверяем поиск пользователя
        auth_service.user_repo.get_by_email.assert_called_once_with(
            "test@example.com")

        # Проверяем создание refresh токена
        auth_service.refresh_repo.create.assert_called_once()
        call_kwargs = auth_service.refresh_repo.create.call_args[1]
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["user_agent"] == "test-agent"
        assert "token_jti" in call_kwargs
        assert "expires_at" in call_kwargs

        # Проверяем коммит
        mock_session.commit.assert_called_once()

        # Проверяем результат
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert isinstance(result["access_token"], str)
        assert len(result["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, valid_login_payload):
        """
        Тест входа с несуществующим email.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        auth_service.user_repo.get_by_email = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(valid_login_payload)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, valid_login_payload, sample_user):
        """
        Тест входа с неверным паролем.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        # Создаём пользователя с другим паролем
        user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash=hash_password("Different123!@#"),
            is_active=True
        )
        auth_service.user_repo.get_by_email = AsyncMock(return_value=user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(valid_login_payload)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, valid_login_payload):
        """
        Тест входа с неактивным пользователем.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        inactive_user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash=hash_password("Test123!@#"),
            is_active=False
        )
        auth_service.user_repo.get_by_email = AsyncMock(
            return_value=inactive_user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(valid_login_payload)

        assert exc_info.value.status_code == 401
        assert "User is inactive" in str(exc_info.value.detail)


# ============================================================================
# Тесты для refresh
# ============================================================================

    @pytest.mark.asyncio
    async def test_refresh_success(
        self, auth_service, mock_session, sample_user, sample_refresh_token
    ):
        """
        Тест успешного обновления токена.

        Проверяет:
        - Декодирование токена
        - Проверка типа токена
        - Поиск refresh токена в БД
        - Проверка, что токен не отозван
        - Проверка активности пользователя
        - Создание нового access токена
        """
        # Arrange
        refresh_token = "valid.refresh.token"

        # Мокаем декодирование
        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123',
                'sub': '1'
            }

            auth_service.refresh_repo.get_by_jti = AsyncMock(
                return_value=sample_refresh_token)
            auth_service.user_repo.get_by_id = AsyncMock(
                return_value=sample_user)

            # Act
            result = await auth_service.refresh(refresh_token)

            # Assert
            mock_decode.assert_called_once_with(refresh_token)
            auth_service.refresh_repo.get_by_jti.assert_called_once_with(
                'test-jti-123')
            auth_service.user_repo.get_by_id.assert_called_once_with(1)

            assert "access_token" in result
            assert result["refresh_token"] == refresh_token
            assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_type(self, auth_service):
        """
        Тест обновления с токеном не refresh типа.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "invalid.token.type"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'access',  # Не refresh!
                'jti': 'test-jti-123',
                'sub': '1'
            }

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh(refresh_token)

            assert exc_info.value.status_code == 401
            assert "Expected refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_revoked(self, auth_service, sample_refresh_token):
        """
        Тест обновления с отозванным refresh токеном.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "revoked.refresh.token"

        # Отзываем токен
        sample_refresh_token.is_revoked = True

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123',
                'sub': '1'
            }

            auth_service.refresh_repo.get_by_jti = AsyncMock(
                return_value=sample_refresh_token)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh(refresh_token)

            assert exc_info.value.status_code == 401
            assert "revoked" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_not_found(self, auth_service):
        """
        Тест обновления с несуществующим refresh токеном.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "nonexistent.refresh.token"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123',
                'sub': '1'
            }

            auth_service.refresh_repo.get_by_jti = AsyncMock(return_value=None)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh(refresh_token)

            assert exc_info.value.status_code == 401
            assert "revoked or not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_user_not_found(self, auth_service, sample_refresh_token):
        """
        Тест обновления, когда пользователь не найден.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "valid.refresh.token"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123',
                'sub': '1'
            }

            auth_service.refresh_repo.get_by_jti = AsyncMock(
                return_value=sample_refresh_token)
            auth_service.user_repo.get_by_id = AsyncMock(return_value=None)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh(refresh_token)

            assert exc_info.value.status_code == 401
            assert "User is inactive" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_user_inactive(self, auth_service, sample_refresh_token):
        """
        Тест обновления, когда пользователь неактивен.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "valid.refresh.token"

        inactive_user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            is_active=False
        )

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123',
                'sub': '1'
            }

            auth_service.refresh_repo.get_by_jti = AsyncMock(
                return_value=sample_refresh_token)
            auth_service.user_repo.get_by_id = AsyncMock(
                return_value=inactive_user)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh(refresh_token)

            assert exc_info.value.status_code == 401
            assert "User is inactive" in str(exc_info.value.detail)


# ============================================================================
# Тесты для logout
# ============================================================================

    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, mock_session):
        """
        Тест успешного выхода.

        Проверяет:
        - Декодирование токена
        - Проверка типа токена
        - Отзыв refresh токена
        - Коммит
        """
        # Arrange
        refresh_token = "valid.refresh.token"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123'
            }

            auth_service.refresh_repo.revoke_by_jti = AsyncMock()

            # Act
            await auth_service.logout(refresh_token)

            # Assert
            mock_decode.assert_called_once_with(refresh_token)
            auth_service.refresh_repo.revoke_by_jti.assert_called_once_with(
                'test-jti-123')
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_invalid_token_type(self, auth_service):
        """
        Тест выхода с токеном не refresh типа.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        refresh_token = "access.token.type"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'access',  # Не refresh!
                'jti': 'test-jti-123'
            }

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.logout(refresh_token)

            assert exc_info.value.status_code == 401
            assert "Expected refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_logout_revoke_error(self, auth_service, mock_session):
        """
        Тест выхода при ошибке отзыва токена.
        """
        # Arrange
        refresh_token = "valid.refresh.token"

        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.return_value = {
                'type': 'refresh',
                'jti': 'test-jti-123'
            }

            auth_service.refresh_repo.revoke_by_jti = AsyncMock(
                side_effect=Exception("Database error"))

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await auth_service.logout(refresh_token)

            assert "Database error" in str(exc_info.value)
            mock_session.commit.assert_not_called()
