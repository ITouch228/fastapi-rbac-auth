"""
Фикстуры для тестов приложения.
Описание: содержат настройки тестовой БД, mock Redis, тестовый HTTP-клиент
и вспомогательные фикстуры для пользователей и авторизации.
"""

from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from factories import RoleFactory, UserFactory
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.access_rule import AccessRoleRule
from app.models.business_element import BusinessElement
from app.repositories.roles import RoleRepository

pytest_plugins = ["pytest_asyncio"]


# =========================================================================
# НАСТРОЙКИ ТЕСТОВОЙ БАЗЫ ДАННЫХ
# =========================================================================

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:1122@localhost:5432/rbac_auth_test"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =========================================================================
# REDIS STUB
# =========================================================================

async def get_redis_stub():
    """Stub Redis для тестов"""
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    yield mock_redis


# =========================================================================
# ФИКСТУРЫ БАЗЫ ДАННЫХ
# =========================================================================

@pytest.fixture(scope="session")
async def setup_database():
    """Фикстура: создание и удаление тестовой БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def apply_setup_database(setup_database):
    """Фикстура: автоматическое применение setup_database"""
    yield


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
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
# ФИКСТУРЫ REDIS
# =========================================================================

@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator:
    """Фикстура: mock Redis клиент"""
    async for redis in get_redis_stub():
        yield redis


# =========================================================================
# ФИКСТУРА HTTP-КЛИЕНТА
# =========================================================================

@pytest.fixture(scope="function")
async def client(
    db_session: AsyncSession,
    redis_client: AsyncGenerator
) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура: тестовый HTTP-клиент FastAPI"""

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield redis_client

    from slowapi import Limiter
    from slowapi.util import get_remote_address

    # Сохраняем исходный limiter
    original_limiter = getattr(app.state, "limiter", None)

    # Отключаем реальное ограничение запросов для тестов
    disabled_limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["999999 per minute"]
    )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_stub] = override_get_redis
    app.state.limiter = disabled_limiter

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_redis_stub, None)

    if original_limiter:
        app.state.limiter = original_limiter


# =========================================================================
# ФИКСТУРЫ ПОЛЬЗОВАТЕЛЕЙ
# =========================================================================

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Фикстура: обычный пользователь с ролью user"""
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()

    role_repo = RoleRepository(db_session)
    user_role = await role_repo.get_by_name("user")

    if not user_role:
        user_role = await RoleFactory.create_async(name="user")

    await role_repo.assign_role(user.id, user_role.id)
    await db_session.commit()

    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """Фикстура: администратор с ролью admin"""
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

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
            AccessRoleRule.element_id == element.id
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
            delete_all_permission=True
        )
        db_session.add(rule)

    await role_repo.assign_role(user.id, admin_role.id)
    await db_session.commit()

    return user


# =========================================================================
# ФИКСТУРЫ АВТОРИЗАЦИИ
# =========================================================================

@pytest.fixture
async def auth_headers(client: AsyncClient, test_user):
    """Фикстура: заголовки авторизации для пользователя"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"}
    )

    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_admin):
    """Фикстура: заголовки авторизации для администратора"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_admin.email, "password": "Test123!@#"}
    )

    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
