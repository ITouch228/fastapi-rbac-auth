from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AccessRoleRule, UserRole
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from tests.factories import (
    BusinessElementFactory,
    RefreshTokenFactory,
    RoleFactory,
    UserFactory,
)

# -------------------- USERS --------------------


class TestUserRepository:

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        await db_session.refresh(user)

        repo = UserRepository(db_session)
        result = await repo.get_by_email(user.email)

        assert result is not None
        assert result.email == user.email
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        await db_session.refresh(user)

        repo = UserRepository(db_session)
        result = await repo.get_by_id(user.id)

        assert result is not None
        assert result.id == user.id

        result_none = await repo.get_by_id(999999)
        assert result_none is None

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = await repo.create(
            full_name="Test User",
            email="test@example.com",
            password_hash="hashed_password"
        )
        await db_session.refresh(user)

        assert user.id is not None
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_update_profile(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async(full_name="Old Name", email="old@example.com")
        await db_session.refresh(user)

        repo = UserRepository(db_session)
        updated = await repo.update_profile(user, full_name="New Name", email=None)
        await db_session.refresh(updated)

        assert updated.full_name == "New Name"
        assert updated.email == "old@example.com"

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async(is_active=True)
        await db_session.refresh(user)

        repo = UserRepository(db_session)
        deleted = await repo.soft_delete(user)
        await db_session.refresh(deleted)

        assert deleted.is_active is False
        assert deleted.deleted_at is not None

        deleted_again = await repo.soft_delete(deleted)
        await db_session.refresh(deleted_again)
        assert deleted_again.is_active is False


# -------------------- ROLES --------------------

class TestRoleRepository:

    @pytest.mark.asyncio
    async def test_get_by_name(self, db_session: AsyncSession):
        RoleFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async(name="admin")
        await db_session.refresh(role)

        repo = RoleRepository(db_session)
        result = await repo.get_by_name("admin")

        assert result is not None
        assert result.name == "admin"

    @pytest.mark.asyncio
    async def test_get_user_roles(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session
        RoleFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        role = await RoleFactory.create_async(name="test_role")
        await db_session.refresh(user)
        await db_session.refresh(role)

        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        await db_session.flush()

        repo = RoleRepository(db_session)
        roles = await repo.get_user_roles(user.id)

        assert len(roles) == 1
        assert roles[0].id == role.id

    @pytest.mark.asyncio
    async def test_assign_single_role(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session
        RoleFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        role1 = await RoleFactory.create_async(name="role1")
        role2 = await RoleFactory.create_async(name="role2")

        repo = RoleRepository(db_session)

        await repo.assign_role(user.id, role1.id)
        roles = await repo.get_user_roles(user.id)
        assert len(roles) == 1 and roles[0].id == role1.id

        await repo.assign_role(user.id, role2.id)
        roles = await repo.get_user_roles(user.id)
        assert len(roles) == 2 and roles[1].id == role2.id

        with pytest.raises(Exception):
            await repo.assign_role(user.id, 999999)


# -------------------- ACCESS RULES --------------------

class TestAccessRuleRepository:

    @pytest.mark.asyncio
    async def test_list_rules(self, db_session: AsyncSession):
        RoleFactory._meta.sqlalchemy_session = db_session
        BusinessElementFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async()
        element = await BusinessElementFactory.create_async()

        rule = AccessRoleRule(
            role_id=role.id, element_id=element.id, read_permission=True)
        db_session.add(rule)
        await db_session.flush()

        repo = AccessRuleRepository(db_session)
        rules = await repo.list_rules()

        assert any(r.id == rule.id for r in rules)

    @pytest.mark.asyncio
    async def test_get_rule(self, db_session: AsyncSession):
        RoleFactory._meta.sqlalchemy_session = db_session
        BusinessElementFactory._meta.sqlalchemy_session = db_session

        role = await RoleFactory.create_async()
        element = await BusinessElementFactory.create_async()

        rule = AccessRoleRule(
            role_id=role.id, element_id=element.id, read_permission=True)
        db_session.add(rule)
        await db_session.flush()

        repo = AccessRuleRepository(db_session)
        result = await repo.get_rule(rule.id)

        assert result is not None
        assert result.id == rule.id

    @pytest.mark.asyncio
    async def test_get_rules_for_roles_and_element(self, db_session: AsyncSession):
        RoleFactory._meta.sqlalchemy_session = db_session
        BusinessElementFactory._meta.sqlalchemy_session = db_session

        role1 = await RoleFactory.create_async()
        role2 = await RoleFactory.create_async()
        element = await BusinessElementFactory.create_async(name="users")

        db_session.add_all([
            AccessRoleRule(role_id=role1.id,
                           element_id=element.id, read_permission=True),
            AccessRoleRule(role_id=role2.id,
                           element_id=element.id, create_permission=True)
        ])
        await db_session.flush()

        repo = AccessRuleRepository(db_session)
        rules = await repo.get_rules_for_roles_and_element([role1.id, role2.id], "users")

        assert len(rules) == 2


# -------------------- TOKENS --------------------

class TestRefreshTokenRepository:

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        repo = RefreshTokenRepository(db_session)

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        token = await repo.create(user_id=user.id, token_jti="jti-123", expires_at=expires_at, user_agent="test")
        await db_session.refresh(token)

        assert token.id is not None

    @pytest.mark.asyncio
    async def test_get_by_jti(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session
        RefreshTokenFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        token = await RefreshTokenFactory.create_async(user_id=user.id, token_jti="jti-456")

        repo = RefreshTokenRepository(db_session)
        result = await repo.get_by_jti("jti-456")
        assert result is not None
        assert result.token_jti == "jti-456"

    @pytest.mark.asyncio
    async def test_revoke_by_jti(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session
        RefreshTokenFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        token = await RefreshTokenFactory.create_async(user_id=user.id, token_jti="jti-789", is_revoked=False)

        repo = RefreshTokenRepository(db_session)
        await repo.revoke_by_jti("jti-789")
        await db_session.refresh(token)

        assert token.is_revoked is True
        assert token.revoked_at is not None

    @pytest.mark.asyncio
    async def test_revoke_all_for_user(self, db_session: AsyncSession):
        UserFactory._meta.sqlalchemy_session = db_session
        RefreshTokenFactory._meta.sqlalchemy_session = db_session

        user = await UserFactory.create_async()
        token1 = await RefreshTokenFactory.create_async(user_id=user.id, is_revoked=False)
        token2 = await RefreshTokenFactory.create_async(user_id=user.id, is_revoked=False)

        repo = RefreshTokenRepository(db_session)
        await repo.revoke_all_for_user(user.id)
        await db_session.refresh(token1)
        await db_session.refresh(token2)

        assert token1.is_revoked is True
        assert token2.is_revoked is True
