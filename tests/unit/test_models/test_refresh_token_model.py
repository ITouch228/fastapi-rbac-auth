"""
Unit тесты для модели RefreshToken.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.refresh_token import RefreshToken


class TestRefreshTokenModel:
    """Unit тесты для модели RefreshToken"""

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_creation(self):
        """Тест: создание refresh токена со всеми полями"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at,
            user_agent="Mozilla/5.0"
        )

        assert token.user_id == 1
        assert token.token_jti == "test-jti-123"
        assert token.expires_at == expires_at
        assert token.user_agent == "Mozilla/5.0"
        assert token.is_revoked is False
        assert token.revoked_at is None
        assert token.id is None
        assert token.created_at is None
        assert token.updated_at is None

    @pytest.mark.unit
    def test_refresh_token_creation_without_user_agent(self):
        """Тест: создание токена без user_agent (опциональное поле)"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at
        )

        assert token.user_agent is None

    @pytest.mark.unit
    def test_refresh_token_default_is_revoked(self):
        """Тест: значение по умолчанию is_revoked = False"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at
        )

        assert token.is_revoked is False
        assert token.revoked_at is None

    @pytest.mark.unit
    def test_refresh_token_creation_with_revoked_state(self):
        """Тест: создание уже отозванного токена"""
        revoked_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at,
            is_revoked=True,
            revoked_at=revoked_at
        )

        assert token.is_revoked is True
        assert token.revoked_at == revoked_at

    # =========================================================================
    # ТЕСТЫ ПРЕОБРАЗОВАНИЯ (TO_DICT)
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_to_dict(self):
        """Тест: преобразование в словарь"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            id=1,
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at,
            is_revoked=False,
            user_agent="Mozilla/5.0"
        )

        token_dict = token.to_dict()

        assert token_dict["id"] == 1
        assert token_dict["user_id"] == 1
        assert token_dict["token_jti"] == "test-jti-123"
        assert token_dict["expires_at"] == expires_at
        assert token_dict["is_revoked"] is False
        assert token_dict["user_agent"] == "Mozilla/5.0"
        assert token_dict["revoked_at"] is None

    @pytest.mark.unit
    def test_refresh_token_to_dict_without_id(self):
        """Тест: to_dict без ID (до сохранения в БД)"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at
        )

        token_dict = token.to_dict()

        assert token_dict["id"] is None
        assert token_dict["user_id"] == 1
        assert token_dict["token_jti"] == "test-jti-123"
        assert token_dict["expires_at"] == expires_at
        assert token_dict["is_revoked"] is False

    @pytest.mark.unit
    def test_refresh_token_to_dict_with_timestamps(self):
        """Тест: to_dict с временными метками"""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        token = RefreshToken(
            id=1,
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at,
            created_at=now,
            updated_at=now
        )

        token_dict = token.to_dict()

        assert token_dict["created_at"] == now
        assert token_dict["updated_at"] == now

    # =========================================================================
    # ТЕСТЫ ОТЗЫВА ТОКЕНА (REVOKE)
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_revoke(self):
        """Тест: отзыв активного токена"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at,
            is_revoked=False
        )

        token.revoke()

        assert token.is_revoked is True
        assert token.revoked_at is not None

    @pytest.mark.unit
    def test_refresh_token_revoke_twice(self):
        """Тест: повторный отзыв токена (не меняет revoked_at)"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at,
            is_revoked=False
        )

        token.revoke()
        revoked_at_first = token.revoked_at

        token.revoke()
        revoked_at_second = token.revoked_at

        assert token.is_revoked is True
        assert revoked_at_first == revoked_at_second

    @pytest.mark.unit
    def test_refresh_token_revoke_already_revoked(self):
        """Тест: отзыв уже отозванного токена (ничего не меняет)"""
        revoked_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at,
            is_revoked=True,
            revoked_at=revoked_at
        )

        token.revoke()

        assert token.is_revoked is True
        assert token.revoked_at == revoked_at

    # =========================================================================
    # ТЕСТЫ ПРОВЕРКИ ИСТЕЧЕНИЯ (IS_EXPIRED)
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_is_expired_with_past_date(self):
        """Тест: токен с истёкшим сроком действия"""
        past = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=past
        )

        assert token.is_expired() is True

    @pytest.mark.unit
    def test_refresh_token_is_expired_with_future_date(self):
        """Тест: токен с будущим сроком действия"""
        future = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=future
        )

        assert token.is_expired() is False

    @pytest.mark.unit
    def test_refresh_token_is_expired_exact_moment(self):
        """Тест: токен, истекающий прямо сейчас (считается истекшим)"""
        now = datetime.now(timezone.utc) - timedelta(microseconds=1)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=now
        )

        assert token.is_expired() is True

    # =========================================================================
    # ТЕСТЫ СТРОКОВОГО ПРЕДСТАВЛЕНИЯ (__REPR__)
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_repr(self):
        """Тест: строковое представление"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-12345678",
            expires_at=expires_at
        )

        repr_str = repr(token)

        assert "RefreshToken" in repr_str
        assert "user_id=1" in repr_str
        assert "test-jti..." in repr_str or "test-jti-12345678" in repr_str
        assert "is_revoked=False" in repr_str

    @pytest.mark.unit
    def test_refresh_token_repr_with_id(self):
        """Тест: строковое представление с ID"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            id=5,
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at
        )

        repr_str = repr(token)

        assert "RefreshToken" in repr_str
        assert "id=5" in repr_str
        assert "user_id=1" in repr_str

    @pytest.mark.unit
    def test_refresh_token_repr_revoked(self):
        """Тест: строковое представление отозванного токена"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test-jti-123",
            expires_at=expires_at,
            is_revoked=True
        )

        repr_str = repr(token)

        assert "RefreshToken" in repr_str
        assert "is_revoked=True" in repr_str

    # =========================================================================
    # ТЕСТЫ ОТНОШЕНИЙ (RELATIONSHIPS)
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_relationships_exist(self):
        """Тест: атрибуты отношений существуют"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at
        )

        assert hasattr(token, 'user')

    @pytest.mark.unit
    def test_refresh_token_relationships_default_value(self):
        """Тест: значение по умолчанию для отношений"""
        token = RefreshToken()

        assert token.user is None

    # =========================================================================
    # ТЕСТЫ TIMESTAMPMIXIN
    # =========================================================================

    @pytest.mark.unit
    def test_timestamp_mixin_fields_exist(self):
        """Тест: наличие полей TimestampMixin"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at
        )

        assert hasattr(token, 'created_at')
        assert hasattr(token, 'updated_at')

    @pytest.mark.unit
    def test_timestamp_mixin_default_values(self):
        """Тест: значения по умолчанию для TimestampMixin"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at
        )

        assert token.created_at is None
        assert token.updated_at is None

    # =========================================================================
    # ТЕСТЫ ТИПОВ ДАННЫХ
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_field_types(self):
        """Тест: типы полей модели"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at,
            is_revoked=False
        )

        assert isinstance(token.user_id, int)
        assert isinstance(token.token_jti, str)
        assert isinstance(token.expires_at, datetime)
        assert isinstance(token.is_revoked, bool)
        assert token.user_agent is None or isinstance(token.user_agent, str)
        assert token.revoked_at is None or isinstance(
            token.revoked_at, datetime)

    # =========================================================================
    # ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ
    # =========================================================================

    @pytest.mark.unit
    def test_refresh_token_jti_max_length(self):
        """Тест: token_jti максимальной длины"""
        long_jti = "a" * 64
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti=long_jti,
            expires_at=expires_at
        )

        assert len(token.token_jti) == 64

    @pytest.mark.unit
    def test_refresh_token_user_agent_max_length(self):
        """Тест: user_agent максимальной длины"""
        long_agent = "A" * 255
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at,
            user_agent=long_agent
        )

        assert len(token.user_agent) == 255

    @pytest.mark.unit
    def test_refresh_token_user_id_min_value(self):
        """Тест: минимальное значение user_id"""
        expires_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token = RefreshToken(
            user_id=1,
            token_jti="test",
            expires_at=expires_at
        )

        assert token.user_id == 1
