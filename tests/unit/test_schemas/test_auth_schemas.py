"""
Unit тесты для Pydantic схем аутентификации.
"""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest


class TestRegisterRequest:
    """Unit тесты для RegisterRequest"""

    @pytest.mark.unit
    def test_valid_register_request(self):
        """Тест: валидный запрос регистрации."""
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "StrongP@ssw0rd123",
            "password_repeat": "StrongP@ssw0rd123"
        }

        request = RegisterRequest(**data)

        assert request.full_name == "Test User"
        assert request.email == "test@example.com"

    @pytest.mark.unit
    def test_passwords_mismatch(self):
        """Тест: пароли не совпадают → ValidationError."""
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "StrongP@ssw0rd123",
            "password_repeat": "Different123!@#"
        }

        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)

        errors = exc.value.errors()
        assert any("Passwords do not match" in err["msg"] for err in errors)

    @pytest.mark.unit
    def test_email_normalization(self):
        """Тест: email нормализуется (strip + lowercase)."""
        data = {
            "full_name": "Test User",
            "email": "  TEST@Example.COM  ",
            "password": "StrongP@ssw0rd123",
            "password_repeat": "StrongP@ssw0rd123"
        }

        request = RegisterRequest(**data)

        assert request.email == "test@example.com"

    @pytest.mark.unit
    def test_password_missing_uppercase(self):
        """Тест: пароль без заглавной буквы → ValidationError."""
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "weakpassword123!",
            "password_repeat": "weakpassword123!"
        }

        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)

        errors = exc.value.errors()
        assert any("uppercase letter" in err["msg"] for err in errors)


class TestLoginRequest:
    """Unit тесты для LoginRequest"""

    @pytest.mark.unit
    def test_valid_login_request(self):
        """Тест: валидный запрос логина."""
        data = {
            "email": "test@example.com",
            "password": "StrongP@ssw0rd123"
        }

        request = LoginRequest(**data)

        assert request.email == "test@example.com"
        assert request.password == "StrongP@ssw0rd123"

    @pytest.mark.unit
    def test_invalid_email(self):
        """Тест: невалидный email → ValidationError."""
        data = {
            "email": "invalid-email",
            "password": "StrongP@ssw0rd123"
        }

        with pytest.raises(ValidationError):
            LoginRequest(**data)
