import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.security import _build_token, create_access_token, create_refresh_token
from app.db.session import get_db

# =========================
# Тесты для get_current_user_optional
# =========================

@pytest.mark.integration
class TestGetCurrentUserOptional:
    """Тесты для get_current_user_optional"""

    async def test_no_token_returns_none(self, db_session: AsyncSession):
        """Без токена → None"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user": user.id if user else None}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.status_code == 200
            assert response.json()["user"] is None

    async def test_valid_token_returns_user(self, db_session: AsyncSession, test_user):
        """Валидный access токен → возвращает пользователя"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user_id": user.id, "user_email": user.email}

        access_token, _, _ = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {access_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == test_user.id
            assert data["user_email"] == test_user.email

    async def test_invalid_token_raises_error(self, db_session: AsyncSession):
        """Невалидный токен → 401"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user_id": user.id}

        headers = {"Authorization": "Bearer invalid_token"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]

    async def test_refresh_token_rejected(self, db_session: AsyncSession, test_user):
        """Refresh токен → 401 (ожидается access)"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user_id": user.id}

        _, refresh_token, _ = create_refresh_token(test_user.id)
        headers = {"Authorization": f"Bearer {refresh_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]

    async def test_user_not_found_raises_error(self, db_session: AsyncSession):
        """Пользователь не найден → 401"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user_id": user.id}

        access_token, _, _ = create_access_token(99999)
        headers = {"Authorization": f"Bearer {access_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401

    async def test_inactive_user_raises_error(self, db_session: AsyncSession, test_user):
        """Неактивный пользователь → 401"""
        test_user.is_active = False
        await db_session.commit()

        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user_optional)):
            return {"user_id": user.id}

        access_token, _, _ = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {access_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "not authenticated" in response.json()["detail"].lower()


# =========================
# Тесты для get_current_user (required)
# =========================

@pytest.mark.integration
class TestGetCurrentUser:
    """Тесты для get_current_user (required)"""

    async def test_valid_token_returns_user(self, db_session: AsyncSession, test_user):
        """Валидный токен → возвращает пользователя"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user)):
            return {"user_id": user.id, "user_email": user.email}

        access_token, _, _ = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {access_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == test_user.id
            assert data["user_email"] == test_user.email

    async def test_no_token_raises_error(self, db_session: AsyncSession):
        """Без токена → 401"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user)):
            return {"user_id": user.id}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]

    async def test_invalid_token_raises_error(self, db_session: AsyncSession):
        """Невалидный токен → 401"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user)):
            return {"user_id": user.id}

        headers = {"Authorization": "Bearer invalid_token"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]

    async def test_refresh_token_rejected(self, db_session: AsyncSession, test_user):
        """Refresh токен → 401"""
        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user)):
            return {"user_id": user.id}

        _, refresh_token, _ = create_refresh_token(test_user.id)
        headers = {"Authorization": f"Bearer {refresh_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]


# =========================
# Реальные API тесты (используют основной app)
# =========================

@pytest.mark.integration
class TestAuthDependenciesWithRealAPI:
    """Тесты зависимостей через реальные API эндпоинты основного приложения"""

    async def test_me_endpoint_with_valid_token(self, client: AsyncClient, auth_headers, test_user):
        """GET /users/me с валидным токеном → возвращает профиль"""
        # login_response = await client.post(
        #     "/api/v1/auth/login",
        #     json={"email": test_user.email, "password": "Test123!@#"}
        # )

        # token = login_response.json()["access_token"]
        # headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    async def test_me_endpoint_without_token(self, client: AsyncClient):
        """GET /users/me без токена → 401"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_me_endpoint_with_invalid_token(self, client: AsyncClient):
        """GET /users/me с невалидным токеном → 401"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    async def test_me_endpoint_with_refresh_token(self, client: AsyncClient, test_user):
        """GET /users/me с refresh токеном → 401"""
        _, refresh_token, _ = create_refresh_token(test_user.id)
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    async def test_me_endpoint_with_inactive_user(self, client: AsyncClient, db_session, test_user):
        """GET /users/me с неактивным пользователем → 401"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "Test123!@#"}
        )
        token = login_response.json()["access_token"]
        test_user.is_active = False
        await db_session.commit()

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_update_me_with_valid_token(self, client: AsyncClient, test_user):
        """PATCH /users/me с валидным токеном → обновляет профиль"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "Test123!@#"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {"full_name": "Updated Name",
                       "email": "updated@example.com"}
        response = await client.patch("/api/v1/users/me", headers=headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    async def test_soft_delete_me_with_valid_token(self, client: AsyncClient, test_user):
        """DELETE /users/me с валидным токеном → удаляет пользователя"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "Test123!@#"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        login_after = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "Test123!@#"}
        )
        assert login_after.status_code == 401
        assert "inactive" in login_after.json()["detail"].lower()


# =========================
# Тесты истечения и отзыва токенов
# =========================

@pytest.mark.integration
class TestTokenExpiration:
    """Тесты истечения токенов"""

    async def test_expired_token_raises_error(self, db_session: AsyncSession, test_user):
        """Просроченный токен → 401"""
        from datetime import timedelta

        app = FastAPI()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/test")
        async def test_endpoint(user=Depends(get_current_user)):
            return {"user_id": user.id}

        access_token, _, _ = _build_token(
            str(test_user.id), 'access', timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test", headers=headers)
            assert response.status_code == 401
            assert "expired" in response.json()["detail"].lower()


@pytest.mark.integration
class TestTokenRevocation:
    """Тесты отзыва токенов"""

    async def test_revoked_refresh_token_cannot_be_used(self, client: AsyncClient, test_user):
        """Отозванный refresh токен → 401 при попытке обновления"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "Test123!@#"}
        )
        refresh_token = login_response.json()["refresh_token"]

        await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()
