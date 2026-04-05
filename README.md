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
-   Создание роли: `10 запросов в минуту`
-   Назначение роли: `5 запросов в минуту`
-   Просмотр списков: `20 запросов в минуту`
-   Обновление правил: `10 запросов в минуту`
-   Регистрация: `3 запроса в час`
-   Вход в систему: `20 запросов в минуту`
-   Обновление токена: `30 запросов в час`
-   Выход из системы: `10 запросов в минуту`

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

400 -> некорректный запрос или невалидные данные
401 -> пользователь не идентифицирован
403 -> пользователь определён, но не имеет доступа
404 -> ресурс не найден
409 -> конфликт данных (например, пользователь уже существует)
422 -> ошибка валидации данных
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
        deps.py
        routes/
          admin.py
          auth.py
          mock_resources.py
          users.py
      core/
        config.py
        exceptions.py
        rate_limiter.py
        security.py
      db/
        base.py
        session.py
      models/
        access_rule.py
        business_element.py
        refresh_token.py
        role.py
        user.py
        user_role.py
      repositories/
        access_rules.py
        base.py
        roles.py
        users.py
      schemas/
        access_rule.py
        auth.py
        common.py
        role.py
        user.py
      services/
        access_service.py
        admin_service.py
        auth_service.py
        user_service.py
      seed/
        seed_data.py
      main.py

    alembic/
    tests/
      unit/
      integration/
    Dockerfile
    docker-compose.yml
    requirements.txt
    requirements-test.txt
    pytest.ini
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

## Запуск локально

1. Создайте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Запустите PostgreSQL и Redis (например, через Docker):
```bash
docker compose up db redis -d
```

5. Примените миграции:
```bash
alembic upgrade head
```

6. Запустите приложение:
```bash
uvicorn app.main:app --reload
```

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
DATABASE_URL

REDIS_URL
REDIS_PASSWORD
RATE_LIMIT_DEFAULT

JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

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

### Управление ролями

POST /admin/roles
GET /admin/roles/{role_name}
PATCH /admin/roles/{role_name}

### Управление правилами доступа

GET /admin/rules
PATCH /admin/rules/{rule_id}

### Управление ролями пользователей

POST /admin/users/{user_id}/roles
GET /admin/users/{user_id}/roles

## Mock ресурсы

/products
/orders
/shops

Поддерживают операции:

GET
GET /{item_id}
POST
PATCH /{item_id}
DELETE /{item_id}

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

# Тестирование

Проект покрыт unit и integration тестами.

## Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Только unit тесты
pytest tests/unit/

# Только integration тесты
pytest tests/integration/

# Конкретный файл
pytest tests/unit/test_services/test_auth_service.py
```

---

# Итог

Решение реализует требования тестового задания:

-   собственная система аутентификации
-   собственная система авторизации (RBAC)
-   таблицы правил доступа в БД
-   тестовые данные
-   admin API для управления ролями и доступом
-   mock бизнес‑ресурсы
-   корректные ответы `401` и `403`
-   rate limiting с использованием Redis
-   healthcheck для мониторинга состояния сервисов
-   покрытие тестами (unit + integration)
