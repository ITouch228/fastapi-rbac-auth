from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import AccessRoleRule, BusinessElement, Role, User, UserRole

logger = logging.getLogger(__name__)

ROLES = [
    ('admin', 'Full access to rules and resources'),
    ('manager', 'Can read all and modify some shared resources'),
    ('user', 'Works with own resources and limited shared resources'),
    ('guest', 'Read-only guest role'),
]

ELEMENTS = [
    ('users', 'Profile and user-related resources'),
    ('products', 'Mock products'),
    ('orders', 'Mock orders'),
    ('shops', 'Mock shops'),
    ('rules', 'RBAC rules administration'),
]

RULES = {
    'admin': {
        'users': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True, delete_permission=True, delete_all_permission=True),
        'products': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True, delete_permission=True, delete_all_permission=True),
        'orders': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True, delete_permission=True, delete_all_permission=True),
        'shops': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True, delete_permission=True, delete_all_permission=True),
        'rules': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True, delete_permission=True, delete_all_permission=True),
    },
    'manager': {
        'users': dict(read_permission=True, update_permission=True),
        'products': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True),
        'orders': dict(read_permission=True, read_all_permission=True, create_permission=True, update_permission=True, update_all_permission=True),
        'shops': dict(read_permission=True, read_all_permission=True),
        'rules': dict(),
    },
    'user': {
        'users': dict(read_permission=True, update_permission=True, delete_permission=True),
        'products': dict(read_permission=True, read_all_permission=True),
        'orders': dict(read_permission=True, create_permission=True, update_permission=True, delete_permission=True),
        'shops': dict(read_permission=True, read_all_permission=True),
        'rules': dict(),
    },
    'guest': {
        'users': dict(),
        'products': dict(read_permission=True, read_all_permission=True),
        'orders': dict(),
        'shops': dict(read_permission=True, read_all_permission=True),
        'rules': dict(),
    },
}

USERS = [
    ('Admin Demo', 'admin@example.com', 'AdminPass123!', 'admin'),
    ('Manager Demo', 'manager@example.com', 'ManagerPass123!', 'manager'),
    ('User Demo', 'user@example.com', 'UserPass123!', 'user'),
    ('Guest Demo', 'guest@example.com', 'GuestPass123!', 'guest'),
]


async def seed(session=None) -> None:
    """Заполнение базы начальными данными (только если их нет)"""
    if session is None:
        async with AsyncSessionLocal() as session:
            await _seed(session)
    else:
        await _seed(session)


async def _seed(session) -> None:
    """Создание ролей, элементов, правил и пользователей (idempotent)"""
    roles_count = await session.scalar(select(func.count(Role.id)))
    if roles_count and roles_count > 0:
        logger.info("Seed skipped: roles already exist (%d found)", roles_count)
        return

    logger.info("Running seed: no roles found in database")

    roles = {}
    for name, description in ROLES:
        role = Role(name=name, description=description)
        session.add(role)
        roles[name] = role

    elements = {}
    for name, description in ELEMENTS:
        element = BusinessElement(name=name, description=description)
        session.add(element)
        elements[name] = element

    await session.flush()

    for role_name, element_rules in RULES.items():
        for element_name, perms in element_rules.items():
            session.add(
                AccessRoleRule(
                    role_id=roles[role_name].id,
                    element_id=elements[element_name].id,
                    read_permission=perms.get('read_permission', False),
                    read_all_permission=perms.get(
                        'read_all_permission', False),
                    create_permission=perms.get('create_permission', False),
                    update_permission=perms.get('update_permission', False),
                    update_all_permission=perms.get(
                        'update_all_permission', False),
                    delete_permission=perms.get('delete_permission', False),
                    delete_all_permission=perms.get(
                        'delete_all_permission', False),
                )
            )

    await session.flush()

    for full_name, email, password, role_name in USERS:
        user = User(full_name=full_name, email=email,
                    password_hash=hash_password(password), is_active=True)
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role_id=roles[role_name].id))

    await session.commit()
    logger.info("Seed completed: roles, elements, rules, and users created")
    logger.info("Seed completed: roles, elements, rules, and users created")


if __name__ == '__main__':
    asyncio.run(seed())
