# Тестовое задание: система аутентификации и авторизации (RBAC)

Реализация тестового задания на **FastAPI + SQLAlchemy 2.0 async +
PostgreSQL + Alembic + JWT**.

Проект реализует собственную систему аутентификации и авторизации
(RBAC) без полной опоры на встроенные механизмы фреймворка.

---

# Используемые технологии

-   FastAPI
-   SQLAlchemy 2.0 (async)
-   asyncpg
-   PostgreSQL
-   Alembic
-   JWT (access + refresh)
-   bcrypt / passlib
-   Docker + docker-compose
-   Redis (для rate limiting)
-   SlowAPI (для rate limiting)
-   Healthchecks (для мониторинга состояния сервисов)

---

# Основные возможности

## Аутентификация

Поддерживаются операции:

-   регистрация пользователя
-   login по email/password
-   refresh/access token
-   logout
-   получение своего профиля
-   обновление профиля
-   мягкое удаление пользователя (soft delete)

Особенности реализации:

-   пароль хранится безопасно как `bcrypt hash`
-   идентификация пользователя происходит через
    `Authorization: Bearer <access_token>`
-   после soft delete пользователь не может снова войти в систему
-   при удалении пользователя все refresh токены инвалидируются

---

# Авторизация (RBAC)

Реализована собственная система контроля доступа.

Основные сущности:

-   роли пользователей
-   бизнес‑элементы системы
-   таблица правил доступа
-   сервис проверки доступа `AccessService`

Поддерживаемые действия:

Read\Create\Update\Delete

Два уровня прав:

*_permission -> действие только со своими объектами
*_all_permission -> действие со всеми объектами

## Логика проверки доступа

Для операций Read\Update\Delete:

1.  Если у роли есть `*_all_permission=True`, доступ разрешается.
2.  Иначе если `*_permission=True` и пользователь является владельцем
    ресурса --- доступ разрешается.
3.  В остальных случаях возвращается **403 Forbidden**.

Для Create:

достаточно `create_permission=True`.

---

# Rate Limiting

В системе реализована защита от чрезмерного использования API с помощью
библиотеки `slowapi` и Redis в качестве хранилища счетчиков.

## Настройки

-   По умолчанию: `1000 запросов в час; 100 запросов в минуту`
-   Для эндпоинта `/health`: `10 запросов в минуту`
-   Для корневого эндпоинта `/`: `5 запросов в минуту`

## Конфигурация

Rate limiting настраивается через переменную окружения `RATE_LIMIT_DEFAULT`,
например: `"1000 per hour;100 per minute"`

При отсутствии подключения к Redis используется in-memory хранилище
(не рекомендуется для production).

---

# Healthcheck

Система предоставляет эндпоинт `/health` для проверки состояния сервиса:

```bash
GET /health
Response: {"status": "ok"}
```

Этот эндпоинт также защищен rate limiting (10 запросов в минуту).

Docker Compose включает healthcheck для всех сервисов:
-   Redis: проверяет возможность выполнения команды `PING`
-   PostgreSQL: проверяет готовность базы данных с помощью `pg_isready`
-   Backend: проверяет доступность эндпоинта `/health`

---

# Коды ответов API

401 -> пользователь не идентифицирован
403 -> пользователь определён, но не имеет доступа
429 -> превышено ограничение на количество запросов (rate limit)

---

# Mock бизнес‑ресурсы

В соответствии с ТЗ реальные таблицы бизнес‑приложения не создаются.

Вместо них реализованы mock endpoints:

/products
/orders
/shops

Эти endpoints:

-   возвращают фиктивные данные
-   проходят через проверку RBAC
-   возвращают `401` или `403` при отсутствии доступа

---

# Схема базы данных

## users

id
full_name
email
password_hash
is_active
deleted_at
created_at
updated_at

## roles

admin
manager
user
guest

## business_elements

users
products
orders
shops
rules

## access_role_rules

Основная таблица RBAC.

role_id
element_id
read_permission
read_all_permission
create_permission
update_permission
update_all_permission
delete_permission
delete_all_permission

## user_roles

Связка пользователей и ролей.

## refresh_tokens

Хранение refresh сессий.

Используется для:

-   logout
-   revoke refresh token
-   инвалидизации токенов при удалении пользователя

---

# Матрица ролей

## admin

Полный доступ ко всем ресурсам и правилам.

## manager

products -> read_all, create, update, update_all
orders -> read_all, create, update, update_all
shops -> read_all

## user

users -> Read/Update/Delete только себя
products -> read_all
orders -> Read/Update/Delete только свои
shops -> read_all

## guest

products -> read_all
shops -> read_all

---

# Структура проекта

    app/
      api/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
      seed/

    alembic/
    Dockerfile
    docker-compose.yml
    requirements.txt
    README.md

---

# Запуск проекта

## Запуск через Docker

Запуск выполняется одной командой:

```bash
docker compose up --build
```

Compose поднимает три сервиса:

db -> PostgreSQL
redis -> Redis сервер для rate limiting
backend -> FastAPI приложение

После запуска документация будет доступна:

```bash
http://localhost:8000/docs
```

Healthcheck эндпоинты:
-   http://localhost:8000/health (для backend)
-   Redis и PostgreSQL также имеют внутренние healthchecks

---

# Переменные окружения

Используются файлы:

.env -> для локального запуска
.env.docker -> для Docker

Основные переменные:

POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT

REDIS_URL
REDIS_PASSWORD
RATE_LIMIT_DEFAULT

JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

REDIS_URL
REDIS_PASSWORD
RATE_LIMIT_DEFAULT

---

# API

Префикс:

/api/v1

## Auth

POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout

## Пользователь

GET /users/me
PATCH /users/me
DELETE /users/me

## Admin API

GET /admin/rules
PATCH /admin/rules/{rule_id}

POST /admin/users/{user_id}/roles
GET /admin/users/{user_id}/roles

## Mock ресурсы

/products
/orders
/shops

Поддерживают операции:

GET
POST
PATCH
DELETE

## Healthcheck

GET /health

---

# Тестовые пользователи

После выполнения seed доступны пользователи:

admin@example.com / AdminPass123!
manager@example.com / ManagerPass123!
user@example.com / UserPass123!
guest@example.com / GuestPass123!

---

# Итог

Решение реализует требования тестового задания:

-   собственная система аутентификации
-   собственная система авторизации (RBAC)
-   таблицы правил доступа в БД
-   тестовые данные
-   admin API для управления доступом
-   mock бизнес‑ресурсы
-   корректные ответы `401` и `403`
-   rate limiting с использованием Redis
-   healthcheck для мониторинга состояния сервисов