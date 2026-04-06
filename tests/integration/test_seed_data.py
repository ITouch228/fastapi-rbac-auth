"""
Integration тесты для seed данных.
Описание: проверяют заполнение базы ролями, элементами,
правилами доступа, пользователями и пользовательскими ролями.
"""

import pytest
from sqlalchemy import delete, func, select

from app.models import AccessRoleRule, BusinessElement, Role, User, UserRole
from app.seed.seed_data import seed


@pytest.mark.integration
class TestSeedData:
    """Integration тесты для seed данных"""

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ SEED ДАННЫХ
    # =========================================================================

    async def test_seed_creates_roles_elements_users_and_rules(self, db_session):
        """Тест: seed создаёт роли, элементы, пользователей и правила доступа"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        roles_count = await db_session.scalar(select(func.count(Role.id)))
        elements_count = await db_session.scalar(select(func.count(BusinessElement.id)))
        users_count = await db_session.scalar(select(func.count(User.id)))
        user_roles_count = await db_session.scalar(select(func.count(UserRole.user_id)))
        rules_count = await db_session.scalar(select(func.count(AccessRoleRule.id)))

        # Проверяем количество созданных записей
        assert roles_count == 4
        assert elements_count == 5
        assert users_count == 4
        assert user_roles_count == 4
        assert rules_count == 20

    async def test_seed_creates_expected_roles(self, db_session):
        """Тест: seed создаёт ожидаемые роли"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(select(Role.name))
        role_names = {row[0] for row in result.all()}

        # Проверяем состав ролей
        assert role_names == {"admin", "manager", "user", "guest"}

    async def test_seed_creates_expected_business_elements(self, db_session):
        """Тест: seed создаёт ожидаемые бизнес-элементы"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(select(BusinessElement.name))
        element_names = {row[0] for row in result.all()}

        # Проверяем состав элементов
        assert element_names == {
            "users", "products", "orders", "shops", "rules"}

    # =========================================================================
    # ТЕСТЫ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЕЙ И РОЛЕЙ
    # =========================================================================

    async def test_seed_creates_expected_users(self, db_session):
        """Тест: seed создаёт ожидаемых пользователей"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(select(User.email))
        emails = {row[0] for row in result.all()}

        # Проверяем состав пользователей
        assert emails == {
            "admin@example.com",
            "manager@example.com",
            "user@example.com",
            "guest@example.com",
        }

    async def test_seed_assigns_correct_roles_to_users(self, db_session):
        """Тест: seed назначает пользователям корректные роли"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(
            select(User.email, Role.name)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
        )
        rows = result.all()

        user_roles = {email: role_name for email, role_name in rows}

        # Проверяем назначенные роли
        assert user_roles["admin@example.com"] == "admin"
        assert user_roles["manager@example.com"] == "manager"
        assert user_roles["user@example.com"] == "user"
        assert user_roles["guest@example.com"] == "guest"

    async def test_seed_stores_password_hashes(self, db_session):
        """Тест: seed сохраняет пароли пользователей в виде хешей"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(select(User))
        users = result.scalars().all()

        # Проверяем, что пароли не хранятся в открытом виде
        assert len(users) == 4

        for user in users:
            assert user.password_hash is not None
            assert user.password_hash != ""
            assert "Pass123!" not in user.password_hash

    # =========================================================================
    # ТЕСТЫ ПРАВ ДОСТУПА
    # =========================================================================

    async def test_seed_creates_full_access_rules_for_admin(self, db_session):
        """Тест: seed создаёт для admin полные права на все элементы"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(
            select(AccessRoleRule)
            .join(Role, Role.id == AccessRoleRule.role_id)
            .where(Role.name == "admin")
        )
        rules = result.scalars().all()

        # Проверяем количество правил admin
        assert len(rules) == 5

        # Проверяем полный набор прав
        for rule in rules:
            assert rule.read_permission is True
            assert rule.read_all_permission is True
            assert rule.create_permission is True
            assert rule.update_permission is True
            assert rule.update_all_permission is True
            assert rule.delete_permission is True
            assert rule.delete_all_permission is True

    async def test_seed_creates_no_rules_access_for_guest_on_rules_element(self, db_session):
        """Тест: seed не даёт guest доступ к элементу rules"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        result = await db_session.execute(
            select(AccessRoleRule)
            .join(Role, Role.id == AccessRoleRule.role_id)
            .join(BusinessElement, BusinessElement.id == AccessRoleRule.element_id)
            .where(
                Role.name == "guest",
                BusinessElement.name == "rules"
            )
        )
        rule = result.scalar_one()

        # Проверяем отсутствие прав
        assert rule.read_permission is False
        assert rule.read_all_permission is False
        assert rule.create_permission is False
        assert rule.update_permission is False
        assert rule.update_all_permission is False
        assert rule.delete_permission is False
        assert rule.delete_all_permission is False

    # =========================================================================
    # ТЕСТЫ ПОВТОРНОГО ЗАПУСКА
    # =========================================================================

    async def test_seed_is_idempotent(self, db_session):
        """Тест: повторный запуск seed не создаёт дубликаты"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)
        await seed(db_session)
        await seed(db_session)

        roles_count = await db_session.scalar(select(func.count(Role.id)))
        elements_count = await db_session.scalar(select(func.count(BusinessElement.id)))
        users_count = await db_session.scalar(select(func.count(User.id)))
        user_roles_count = await db_session.scalar(select(func.count(UserRole.user_id)))
        rules_count = await db_session.scalar(select(func.count(AccessRoleRule.id)))

        # Проверяем, что дубликаты не появились
        assert roles_count == 4
        assert elements_count == 5
        assert users_count == 4
        assert user_roles_count == 4
        assert rules_count == 20

    # =========================================================================
    # ТЕСТЫ ПОВЕДЕНИЯ ПРИ НАЛИЧИИ ДАННЫХ
    # =========================================================================

    async def test_seed_skips_when_data_exists(self, db_session):
        """Тест: seed пропускает заполнение если данные уже есть"""
        for model in (UserRole, AccessRoleRule, User, BusinessElement, Role):
            await db_session.execute(delete(model))
        await db_session.commit()

        await seed(db_session)

        roles_count_before = await db_session.scalar(select(func.count(Role.id)))
        assert roles_count_before == 4

        await seed(db_session)

        roles_count_after = await db_session.scalar(select(func.count(Role.id)))
        assert roles_count_after == roles_count_before
