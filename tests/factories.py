from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import factory
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.access_rule import AccessRoleRule
from app.models.business_element import BusinessElement
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User

fake = Faker()


class AsyncSQLAlchemyFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Базовая асинхронная фабрика для SQLAlchemy"""

    class Meta:
        abstract = True
        sqlalchemy_session: Optional[AsyncSession] = None
        sqlalchemy_session_persistence = "flush"

    @classmethod
    def _get_session(cls) -> AsyncSession:
        session = cls._meta.sqlalchemy_session
        if session is None:
            raise RuntimeError(
                f"{cls.__name__}: sqlalchemy_session is not set")
        return session

    @classmethod
    async def create_async(cls, **kwargs) -> Any:
        session = cls._get_session()
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.flush()
        return obj

    @classmethod
    async def create_batch_async(cls, size: int, **kwargs) -> List[Any]:
        session = cls._get_session()
        objs = [cls.build(**kwargs) for _ in range(size)]
        session.add_all(objs)
        await session.flush()
        return objs


# =====================
# Фабрики для моделей
# =====================

class UserFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.email())
    full_name = factory.LazyAttribute(lambda _: fake.name())
    password_hash = factory.LazyFunction(lambda: hash_password("Test123!@#"))
    is_active = True
    deleted_at = None


class RoleFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Role

    name = factory.LazyAttribute(lambda _: fake.unique.word())
    description = factory.LazyAttribute(lambda _: fake.sentence())


class BusinessElementFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = BusinessElement

    name = factory.LazyAttribute(lambda _: fake.unique.word())
    description = factory.LazyAttribute(lambda _: fake.sentence())


class AccessRuleFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = AccessRoleRule

    read_permission = False
    read_all_permission = False
    create_permission = False
    update_permission = False
    update_all_permission = False
    delete_permission = False
    delete_all_permission = False


class RefreshTokenFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = RefreshToken

    token_jti = factory.LazyAttribute(lambda _: fake.uuid4())
    expires_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )
    is_revoked = False
    revoked_at = None
    user_agent = "test-agent"
