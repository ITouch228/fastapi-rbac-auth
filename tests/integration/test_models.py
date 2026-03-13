from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.access_rule import AccessRoleRule
from app.models.business_element import BusinessElement
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from tests.factories import (
    AccessRuleFactory,
    BusinessElementFactory,
    RefreshTokenFactory,
    RoleFactory,
    UserFactory,
)

# =========================
# USER
# =========================

@pytest.mark.asyncio
async def test_user_creation(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    user = await UserFactory.create_async()

    assert user.id is not None
    assert user.full_name
    assert user.email
    assert user.password_hash
    assert user.is_active is True


@pytest.mark.asyncio
async def test_user_email_unique_constraint(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    await UserFactory.create_async(email="test@example.com")

    with pytest.raises(IntegrityError):
        await UserFactory.create_async(email="test@example.com")


@pytest.mark.asyncio
async def test_user_relationships(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    user = await UserFactory.create_async()

    result = await db_session.execute(
        select(User)
        .options(selectinload(User.roles), selectinload(User.refresh_tokens))
        .where(User.id == user.id)
    )
    user = result.scalar_one()

    assert hasattr(user, "roles")
    assert hasattr(user, "refresh_tokens")


# =========================
# ROLE
# =========================

@pytest.mark.asyncio
async def test_role_creation(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    role = await RoleFactory.create_async()

    assert role.id is not None
    assert role.name
    assert isinstance(role.name, str)


@pytest.mark.asyncio
async def test_role_name_unique_constraint(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    await RoleFactory.create_async(name="admin")

    with pytest.raises(IntegrityError):
        await RoleFactory.create_async(name="admin")


@pytest.mark.asyncio
async def test_role_relationships(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    role = await RoleFactory.create_async()

    result = await db_session.execute(
        select(Role)
        .options(selectinload(Role.users), selectinload(Role.rules))
        .where(Role.id == role.id)
    )
    role = result.scalar_one()

    assert hasattr(role, "users")
    assert hasattr(role, "rules")


# =========================
# BUSINESS ELEMENT
# =========================

@pytest.mark.asyncio
async def test_business_element_creation(db_session: AsyncSession):
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    element = await BusinessElementFactory.create_async()

    assert element.id is not None
    assert element.name
    assert isinstance(element.name, str)


@pytest.mark.asyncio
async def test_business_element_name_unique_constraint(db_session: AsyncSession):
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    await BusinessElementFactory.create_async(name="users")

    with pytest.raises(IntegrityError):
        await BusinessElementFactory.create_async(name="users")


@pytest.mark.asyncio
async def test_business_element_relationships(db_session: AsyncSession):
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    element = await BusinessElementFactory.create_async()

    result = await db_session.execute(
        select(BusinessElement)
        .options(selectinload(BusinessElement.rules))
        .where(BusinessElement.id == element.id)
    )
    element = result.scalar_one()

    assert hasattr(element, "rules")


# =========================
# ACCESS RULE
# =========================

@pytest.mark.asyncio
async def test_access_rule_creation(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    AccessRuleFactory._meta.sqlalchemy_session = db_session

    role = await RoleFactory.create_async()
    element = await BusinessElementFactory.create_async()
    rule = await AccessRuleFactory.create_async(
        role_id=role.id,
        element_id=element.id,
        read_permission=True,
        create_permission=True,
    )

    assert rule.id is not None
    assert rule.role_id == role.id
    assert rule.element_id == element.id
    assert rule.read_permission is True
    assert rule.create_permission is True


@pytest.mark.asyncio
async def test_access_rule_unique_constraint(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    AccessRuleFactory._meta.sqlalchemy_session = db_session

    role = await RoleFactory.create_async()
    element = await BusinessElementFactory.create_async()
    await AccessRuleFactory.create_async(role_id=role.id, element_id=element.id)

    with pytest.raises(IntegrityError):
        await AccessRuleFactory.create_async(role_id=role.id, element_id=element.id)


@pytest.mark.asyncio
async def test_access_rule_relationships(db_session: AsyncSession):
    RoleFactory._meta.sqlalchemy_session = db_session
    BusinessElementFactory._meta.sqlalchemy_session = db_session
    AccessRuleFactory._meta.sqlalchemy_session = db_session

    role = await RoleFactory.create_async()
    element = await BusinessElementFactory.create_async()
    rule = await AccessRuleFactory.create_async(role_id=role.id, element_id=element.id)

    result = await db_session.execute(
        select(AccessRoleRule)
        .options(selectinload(AccessRoleRule.role), selectinload(AccessRoleRule.element))
        .where(AccessRoleRule.id == rule.id)
    )
    rule = result.scalar_one()

    assert hasattr(rule, "role")
    assert hasattr(rule, "element")


# =========================
# REFRESH TOKEN
# =========================

@pytest.mark.asyncio
async def test_refresh_token_creation(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    RefreshTokenFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()
    token = await RefreshTokenFactory.create_async(
        user_id=user.id,
        token_jti="test-jti-token",
        expires_at=datetime.now(timezone.utc),
    )

    assert token.id is not None
    assert token.user_id == user.id
    assert token.token_jti == "test-jti-token"
    assert token.expires_at


@pytest.mark.asyncio
async def test_refresh_token_relationships(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    RefreshTokenFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()
    token = await RefreshTokenFactory.create_async(
        user_id=user.id,
        token_jti="test-jti-token",
        expires_at=datetime.now(timezone.utc),
    )

    result = await db_session.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.id == token.id)
    )
    token = result.scalar_one()

    assert hasattr(token, "user")


# =========================
# USER ROLE
# =========================

@pytest.mark.asyncio
async def test_user_role_creation(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()
    role = await RoleFactory.create_async()
    user_role = UserRole(user_id=user.id, role_id=role.id)

    db_session.add(user_role)
    await db_session.flush()

    assert user_role.id is not None
    assert user_role.user_id == user.id
    assert user_role.role_id == role.id


@pytest.mark.asyncio
async def test_user_role_unique_constraint(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()
    role = await RoleFactory.create_async()

    user_role1 = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role1)
    await db_session.flush()

    user_role2 = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_user_role_relationships(db_session: AsyncSession):
    UserFactory._meta.sqlalchemy_session = db_session
    RoleFactory._meta.sqlalchemy_session = db_session

    user = await UserFactory.create_async()
    role = await RoleFactory.create_async()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.flush()

    result = await db_session.execute(
        select(UserRole)
        .options(selectinload(UserRole.user), selectinload(UserRole.role))
        .where(UserRole.id == user_role.id)
    )
    user_role = result.scalar_one()

    assert hasattr(user_role, "user")
    assert hasattr(user_role, "role")
