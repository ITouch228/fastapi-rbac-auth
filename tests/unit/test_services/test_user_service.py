"""
Unit тесты для UserService.

Тестируют бизнес-логику управления пользователями в изоляции от реальных зависимостей.
Все внешние зависимости (репозитории, БД) заменены на моки.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdateRequest
from app.services.user_service import UserService


class TestUserService:
    """Unit тесты для UserService с моками"""

    @pytest.fixture
    def mock_session(self):
        """Мок сессии базы данных"""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def user_service(self, mock_session):
        """Создание UserService с моками"""
        service = UserService(mock_session)
        # Мокаем репозитории
        service.user_repo = AsyncMock()
        service.refresh_repo = AsyncMock()
        return service

    @pytest.fixture
    def sample_user(self):
        """Создание тестового пользователя"""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password",
            is_active=True
        )

    @pytest.fixture
    def inactive_user(self):
        """Создание неактивного пользователя"""
        return User(
            id=2,
            email="inactive@example.com",
            full_name="Inactive User",
            password_hash="hashed_password",
            is_active=False
        )

    @pytest.fixture
    def another_user(self):
        """Создание другого пользователя"""
        return User(
            id=3,
            email="other@example.com",
            full_name="Other User",
            password_hash="hashed_password",
            is_active=True
        )


# ============================================================================
# Тесты для get_current
# ============================================================================


    @pytest.mark.asyncio
    async def test_get_current_success(self, user_service, sample_user):
        """
        Тест успешного получения текущего пользователя.

        Проверяет:
        - Пользователь существует
        - Пользователь активен
        """
        # Act
        result = await user_service.get_current(sample_user)

        # Assert
        assert result == sample_user
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_get_current_user_none(self, user_service):
        """
        Тест получения текущего пользователя, когда пользователь None.

        Ожидаемый результат: HTTPException 401
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_current(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, user_service, inactive_user):
        """
        Тест получения текущего пользователя, когда пользователь неактивен.

        Ожидаемый результат: HTTPException 401
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_current(inactive_user)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)


# ============================================================================
# Тесты для update_me
# ============================================================================


    @pytest.mark.asyncio
    async def test_update_me_success(self, user_service, mock_session, sample_user):
        """
        Тест успешного обновления профиля.

        Проверяет:
        - Пользователь активен
        - Обновление полей
        - Сохранение в БД
        """
        # Arrange
        payload = UserUpdateRequest(
            full_name="Updated Name",
            email="updated@example.com"
        )

        # Мокаем, что email не занят
        user_service.user_repo.get_by_email = AsyncMock(return_value=None)

        # Мокаем обновление
        updated_user = User(
            id=1,
            full_name="Updated Name",
            email="updated@example.com",
            is_active=True
        )
        user_service.user_repo.update_profile = AsyncMock(
            return_value=updated_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        # Проверяем проверку email
        user_service.user_repo.get_by_email.assert_called_once_with(
            "updated@example.com")

        # Проверяем обновление
        user_service.user_repo.update_profile.assert_called_once_with(
            sample_user,
            full_name="Updated Name",
            email="updated@example.com"
        )

        # Проверяем коммит
        mock_session.commit.assert_called_once()

        # Проверяем результат
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_me_only_full_name(self, user_service, mock_session, sample_user):
        """
        Тест обновления только имени.
        """
        # Arrange
        payload = UserUpdateRequest(full_name="Updated Name")

        # Мокаем обновление
        updated_user = User(
            id=1,
            full_name="Updated Name",
            email=sample_user.email,
            is_active=True
        )
        user_service.user_repo.update_profile = AsyncMock(
            return_value=updated_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        user_service.user_repo.update_profile.assert_called_once_with(
            sample_user,
            full_name="Updated Name",
            email=None
        )
        assert result.full_name == "Updated Name"
        assert result.email == sample_user.email

    @pytest.mark.asyncio
    async def test_update_me_only_email(self, user_service, mock_session, sample_user):
        """
        Тест обновления только email.
        """
        # Arrange
        payload = UserUpdateRequest(email="new@example.com")

        # Мокаем, что email не занят
        user_service.user_repo.get_by_email = AsyncMock(return_value=None)

        # Мокаем обновление
        updated_user = User(
            id=1,
            full_name=sample_user.full_name,
            email="new@example.com",
            is_active=True
        )
        user_service.user_repo.update_profile = AsyncMock(
            return_value=updated_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        user_service.user_repo.get_by_email.assert_called_once_with(
            "new@example.com")
        user_service.user_repo.update_profile.assert_called_once_with(
            sample_user,
            full_name=None,
            email="new@example.com"
        )
        assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_me_email_already_exists(self, user_service, sample_user, another_user):
        """
        Тест обновления email на уже существующий.

        Ожидаемый результат: HTTPException 400
        """
        # Arrange
        payload = UserUpdateRequest(email="other@example.com")

        # Мокаем, что email занят другим пользователем
        user_service.user_repo.get_by_email = AsyncMock(
            return_value=another_user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_me(sample_user, payload)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

        # Проверяем, что обновление не вызывалось
        user_service.user_repo.update_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_me_same_email(self, user_service, mock_session, sample_user):
        """
        Тест обновления с тем же email (не проверяем уникальность).
        """
        # Arrange
        payload = UserUpdateRequest(email=sample_user.email)

        # Мокаем обновление
        user_service.user_repo.update_profile = AsyncMock(
            return_value=sample_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        # Не должно быть проверки email (так как email не изменился)
        user_service.user_repo.get_by_email.assert_not_called()

        # Обновление должно быть вызвано
        user_service.user_repo.update_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_me_user_none(self, user_service):
        """
        Тест обновления, когда пользователь None.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        payload = UserUpdateRequest(full_name="Updated Name")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_me(None, payload)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_user_inactive(self, user_service, inactive_user):
        """
        Тест обновления, когда пользователь неактивен.

        Ожидаемый результат: HTTPException 401
        """
        # Arrange
        payload = UserUpdateRequest(full_name="Updated Name")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_me(inactive_user, payload)

        assert exc_info.value.status_code == 401


# ============================================================================
# Тесты для soft_delete_me
# ============================================================================


    @pytest.mark.asyncio
    async def test_soft_delete_me_success(self, user_service, mock_session, sample_user):
        """
        Тест успешного мягкого удаления пользователя.

        Проверяет:
        - Пользователь активен
        - Мягкое удаление пользователя
        - Отзыв всех refresh токенов
        - Коммит
        """
        # Arrange
        user_service.user_repo.soft_delete = AsyncMock()
        user_service.refresh_repo.revoke_all_for_user = AsyncMock()

        # Act
        await user_service.soft_delete_me(sample_user)

        # Assert
        user_service.user_repo.soft_delete.assert_called_once_with(sample_user)
        user_service.refresh_repo.revoke_all_for_user.assert_called_once_with(
            1)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_me_user_none(self, user_service):
        """
        Тест удаления, когда пользователь None.

        Ожидаемый результат: HTTPException 401
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.soft_delete_me(None)

        assert exc_info.value.status_code == 401

        # Проверяем, что удаление не вызывалось
        user_service.user_repo.soft_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_delete_me_user_inactive(self, user_service, inactive_user):
        """
        Тест удаления, когда пользователь неактивен.

        Ожидаемый результат: HTTPException 401
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.soft_delete_me(inactive_user)

        assert exc_info.value.status_code == 401

        # Проверяем, что удаление не вызывалось
        user_service.user_repo.soft_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_delete_me_revokes_all_tokens(self, user_service, mock_session, sample_user):
        """
        Тест: при удалении пользователя отзываются все его refresh токены.
        """
        # Arrange
        user_service.user_repo.soft_delete = AsyncMock()
        user_service.refresh_repo.revoke_all_for_user = AsyncMock()

        # Act
        await user_service.soft_delete_me(sample_user)

        # Assert
        user_service.refresh_repo.revoke_all_for_user.assert_called_once_with(
            1)
        mock_session.commit.assert_called_once()


# ============================================================================
# Тесты для update_me с комбинациями полей
# ============================================================================


    @pytest.mark.asyncio
    async def test_update_me_empty_payload(self, user_service, mock_session, sample_user):
        """
        Тест обновления с пустым payload.

        Проверяет, что обновление вызывается с None значениями.
        """
        # Arrange
        payload = UserUpdateRequest()  # все поля None

        # Мокаем обновление
        user_service.user_repo.update_profile = AsyncMock(
            return_value=sample_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        user_service.user_repo.update_profile.assert_called_once_with(
            sample_user,
            full_name=None,
            email=None
        )
        mock_session.commit.assert_called_once()
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_update_me_duplicate_email_different_case(self, user_service, sample_user, another_user):
        """
        Тест обновления email на email с другим регистром, который уже существует.

        Проверяет, что проверка регистронезависима.
        """
        # Arrange
        payload = UserUpdateRequest(email="OTHER@example.com")

        # Мокаем, что email (в нижнем регистре) уже существует
        user_service.user_repo.get_by_email = AsyncMock(
            return_value=another_user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_me(sample_user, payload)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_me_update_own_email(self, user_service, mock_session, sample_user):
        """
        Тест обновления email на тот же email (обновление самого себя).

        Проверяет, что проверка уникальности не выполняется,
        если обновляемый пользователь и есть владелец email.
        """
        # Arrange
        payload = UserUpdateRequest(email=sample_user.email)

        # Мокаем обновление
        user_service.user_repo.update_profile = AsyncMock(
            return_value=sample_user)

        # Act
        result = await user_service.update_me(sample_user, payload)

        # Assert
        # Не должно быть проверки email
        user_service.user_repo.get_by_email.assert_not_called()
        user_service.user_repo.update_profile.assert_called_once()
