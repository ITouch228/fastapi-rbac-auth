"""
Фикстуры для тестов приложения.

Содержит:
- Настройки тестовой базы данных
- Mock Redis для rate limiting
- Тестовый HTTP-клиент FastAPI
- Вспомогательные фикстуры для пользователей и авторизации

Используется для:
- Создания и очистки тестовой БД перед запуском тестов
- Изоляции тестов через транзакции с автоматическим откатом
- Подмены зависимостей приложения (БД, rate limiter)
- Создания тестовых пользователей с корректными ролями
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.access_rule import AccessRoleRule
from app.models.business_element import BusinessElement
from app.models.user import User
from app.repositories.roles import RoleRepository

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:1122@localhost:5432/rbac_auth_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


# =========================================================================
# НАСТРОЙКИ ТЕСТОВОЙ БАЗЫ ДАННЫХ
# =========================================================================


@pytest.fixture(scope="session")
async def setup_database():
    """Фикстура: создание и удаление тестовой БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура: сессия БД с откатом транзакции после теста"""
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


# =========================================================================
# MOCK REDIS
# =========================================================================


@pytest.fixture
def mock_redis():
    """Фикстура: mock Redis клиент для обхода rate limiting"""
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.get.return_value = None
    redis.set.return_value = True
    return redis


# =========================================================================
# ФИКСТУРА HTTP-КЛИЕНТА
# =========================================================================


@pytest.fixture
async def client(
    db_session: AsyncSession,
    mock_redis: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура: тестовый HTTP-клиент FastAPI"""
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    original_limiter = getattr(app.state, "limiter", None)
    disabled_limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["999999 per minute"],
        storage_uri="memory://",
    )
    app.state.limiter = disabled_limiter

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    app.state.limiter = original_limiter


# =========================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ФАБРИК
# =========================================================================


@asynccontextmanager
async def with_factory_session(session: AsyncSession):
    """Контекст-менеджер для безопасной установки сессии фабрик"""
    from factories import RoleFactory, UserFactory

    original_user_session = UserFactory._meta.sqlalchemy_session
    original_role_session = RoleFactory._meta.sqlalchemy_session

    UserFactory._meta.sqlalchemy_session = session
    RoleFactory._meta.sqlalchemy_session = session

    try:
        yield
    finally:
        UserFactory._meta.sqlalchemy_session = original_user_session
        RoleFactory._meta.sqlalchemy_session = original_role_session


# =========================================================================
# ФИКСТУРЫ ПОЛЬЗОВАТЕЛЕЙ
# =========================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Фикстура: обычный пользователь с ролью user"""
    from factories import RoleFactory, UserFactory

    async with with_factory_session(db_session):
        user = await UserFactory.create_async()

        role_repo = RoleRepository(db_session)
        user_role = await role_repo.get_by_name("user")

        if not user_role:
            user_role = await RoleFactory.create_async(name="user")

        await role_repo.assign_role(user.id, user_role.id)

    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """Фикстура: администратор с ролью admin"""
    from factories import RoleFactory, UserFactory

    async with with_factory_session(db_session):
        user = await UserFactory.create_async(email="admin@example.com")

        role_repo = RoleRepository(db_session)
        admin_role = await role_repo.get_by_name("admin")

        if not admin_role:
            admin_role = await RoleFactory.create_async(name="admin")

        result = await db_session.execute(
            select(BusinessElement).where(BusinessElement.name == "rules")
        )
        element = result.scalar_one_or_none()

        if not element:
            element = BusinessElement(name="rules", description="Access rules")
            db_session.add(element)
            await db_session.flush()

        result = await db_session.execute(
            select(AccessRoleRule).where(
                AccessRoleRule.role_id == admin_role.id,
                AccessRoleRule.element_id == element.id,
            )
        )
        rule = result.scalar_one_or_none()

        if not rule:
            rule = AccessRoleRule(
                role_id=admin_role.id,
                element_id=element.id,
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
                delete_permission=True,
                delete_all_permission=True,
            )
            db_session.add(rule)

        await role_repo.assign_role(user.id, admin_role.id)

    return user


# =========================================================================
# ФИКСТУРЫ АВТОРИЗАЦИИ
# =========================================================================


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User):
    """Фикстура: заголовки авторизации для пользователя"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_admin: User):
    """Фикстура: заголовки авторизации для администратора"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_admin.email, "password": "Test123!@#"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
