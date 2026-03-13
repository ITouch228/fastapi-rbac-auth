# RBAC Auth Service

Система аутентификации и авторизации (RBAC) на FastAPI: JWT access/refresh токены, таблица правил доступа в БД, rate limiting через Redis, soft delete пользователей, mock бизнес-ресурсы для проверки прав.

![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Redis](https://img.shields.io/badge/Redis-7-DC382D)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED)
![Coverage](https://img.shields.io/badge/coverage-76%25-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Результат

**193 unit-теста** проходят, покрытие **76%**, ruff — 0 ошибок.

```text
193 passed in 10.69s

TOTAL                                 1054    254    76%

=== Code Quality Report ===
✅ Ruff (lint)
✅ Ruff (format)
```

---

## Как это работает

Пользователь регистрируется и логинится — сервер выдаёт пару JWT (access + refresh) на HS256. Refresh-токены хранятся в БД с JTI — при logout или soft delete все сессии инвалидируются. Авторизация работает через RBAC: у пользователя есть роли, у ролей — правила доступа к бизнес-элементам (products, orders, shops, users, rules). Каждое правило определяет право на действие (read/create/update/delete) и уровень (свои / все ресурсы). Mock-ресурсы (/products, /orders, /shops) демонстрируют работу RBAC без реальной бизнес-логики.

---

## Быстрый старт

Через Docker (рекомендуется):

```bash
git clone git@github.com:ITouch228/fastapi-rbac-auth.git
cd fastapi-rbac-auth

cp .env.example .env
cp .env.docker.example .env.docker   # заполнить JWT_SECRET_KEY, пароли

docker compose up --build -d
```

- API docs — http://localhost:8000/docs
- Health — http://localhost:8000/health

После запуска миграции применяются автоматически (entrypoint.sh). Для seed данных:

```bash
docker compose exec backend python -m app.seed.seed_data
```

Без Docker:

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # заполнить
docker compose up db redis -d         # поднять PostgreSQL + Redis
alembic upgrade head
python -m app.seed.seed_data
uvicorn app.main:app --reload
```

---

## Стек

**Backend**
- **Python** 3.12
- **FastAPI** 0.116 — async-роуты, middleware, dependency injection
- **SQLAlchemy** 2.0 (async) + **asyncpg** — ORM и драйвер PostgreSQL
- **Alembic** — миграции
- **PyJWT** — JWT access/refresh (HS256)
- **bcrypt** — хеширование паролей
- **pydantic-settings** — env-driven конфигурация
- **SlowAPI + Redis** — rate limiting
- **Ruff** (lint + format)

**Инфраструктура**
- **Docker** + **docker-compose** — PostgreSQL 16 + Redis 7 + backend
- **Makefile** — команды разработки
- **Healthchecks** — все сервисы monitored

---

## Архитектура

Слоистая: `routes → services → repositories → database`. Роуты не знают про SQL, сервисы не знают про HTTP.

**Backend** (`app/`):
- `api/` — зависимости (`deps.py`) + роуты (auth, users, admin, mock_resources)
- `services/` — бизнес-логика (auth, user, admin, access)
- `repositories/` — слой доступа к БД (users, roles, access_rules, refresh_tokens)
- `models/` — SQLAlchemy-модели (User, Role, BusinessElement, AccessRoleRule, UserRole, RefreshToken)
- `schemas/` — Pydantic-схемы (DTO, изоляция от БД)
- `core/` — конфигурация, безопасность, rate limiter, исключения
- `db/` — engine, session factory
- `seed/` — идемпотентное заполнение БД

### Ключевые решения

- **Собственная RBAC через таблицу правил.** Не `role = admin` в if-else, а нормализованная таблица `access_role_rules` с булевыми флагами на каждое действие × элемент × уровень (own/all). Добавление новой роли — INSERT, без правки кода.
- **Два уровня прав: `*_permission` vs `*_all_permission`.** `update_permission` — обновлять свои ресурсы; `update_all_permission` — любые. Проверка через `resource_owner_id == user.id`.
- **Refresh-токены в БД с JTI.** Logout и soft delete инвалидируют все refresh-сессии пользователя через `UPDATE SET is_revoked=True`. Access-токены живут 15 минут — компрометация ограничена.
- **Rate limiting с Redis как backend.** SlowAPI + Redis для распределённых счётчиков. В debug mode — in-memory fallback; в production — Redis обязателен (без него приложение не стартует).
- **Soft delete + cascade revoke.** `deleted_at` вместо `DELETE` — пользователь не может войти, все refresh-токены отозваны.
- **JWT с полным набором проверок.** `decode_token` валидирует подпись, exp, iat, nbf, обязательные claims (sub, type, jti). Каждый тип ошибки — отдельное сообщение.
- **Validation JWT_SECRET_KEY ≥ 32 символов.** На старте приложения — если ключ короткий и `DEBUG=false`, приложение падает с `RuntimeError`.
- **CORS validation на старте.** В production пустой `CORS_ORIGINS` → `ValueError`. В debug — пустой список (без CORS middleware ограничений).
- **Идемпотентный seed.** `seed()` проверяет `count(Role.id)` — повторный запуск не создаёт дубликаты.

### Что решалось по ходу

- **Mock-ресурсы для демонстрации RBAC.** Реальные таблицы бизнес-приложения не нужны — эндпоинты возвращают фиктивные данные, но проходят через `AccessService.check_access()`. Это позволяет тестировать матрицу прав без привязки к предметной области.
- **OR-логика правил.** У пользователя может быть несколько ролей — если хотя бы одна даёт доступ, операция разрешена. Итерация по всем правилам, `return True` на первом совпадении.
- **`get_current_user_optional` vs `get_current_user`.** Mock-ресурсы используют optional-версию — неавторизованный пользователь получает 401 от `AccessService`, а не от FastAPI-зависимости. Это даёт единообразные ответы.
- **Формат rate_limit_default через `;`.** SlowAPI принимает список лимитов; Pydantic не парсит `;`-разделённую строку нативно — передаётся как есть в `default_limits=[...]`.
- **In-memory fallback для Redis только в debug.** В production Redis обязателен — иначе rate limiting не работает между репликами.

---

## Модель данных

```text
User (id, full_name, email, password_hash, is_active, deleted_at)
 ├─ UserRole ──→ Role (id, name, description)
 │                  └─ AccessRoleRule (role_id, element_id, read/create/update/delete + *_all)
 │                       └─ BusinessElement (id, name, description)
 └─ RefreshToken (id, user_id, token_jti, expires_at, is_revoked, user_agent)
```

---

## API

Все роуты под префиксом `/api/v1`.

### Auth

| Метод | URL | Описание | Rate limit |
|-------|-----|----------|------------|
| POST | `/auth/register` | Регистрация | 3/час |
| POST | `/auth/login` | Логин → access + refresh | 20/мин |
| POST | `/auth/refresh` | Обновить пару токенов | 30/час |
| POST | `/auth/logout` | Отозвать refresh-токен | 10/мин |

### Users

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/users/me` | Текущий профиль |
| PATCH | `/users/me` | Обновить профиль |
| DELETE | `/users/me` | Soft delete |

### Admin (RBAC)

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/admin/roles` | Создать роль |
| GET | `/admin/roles/{name}` | Роль по имени |
| PATCH | `/admin/roles/{name}` | Обновить роль |
| GET | `/admin/users/{id}/roles` | Роли пользователя |
| POST | `/admin/users/{id}/roles` | Назначить роль |
| GET | `/admin/rules` | Список правил доступа |
| PATCH | `/admin/rules/{id}` | Обновить правило |

### Mock ресурсы

| Ресурс | Операции |
|--------|----------|
| `/products` | GET, GET/{id}, POST, PATCH/{id}, DELETE/{id} |
| `/orders` | GET, GET/{id}, POST, PATCH/{id}, DELETE/{id} |
| `/shops` | GET, GET/{id}, POST, PATCH/{id}, DELETE/{id} |

### Health

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/health` | {"status": "ok"} |

Все эндпоинты, кроме auth и health, требуют `Authorization: Bearer <access>`.

### Матрица ролей

| Роль | products | orders | shops | users | rules |
|------|----------|--------|-------|-------|-------|
| admin | CRUD all | CRUD all | CRUD all | CRUD all | CRUD all |
| manager | read_all, create, update_all | read_all, create, update_all | read_all | read, update (own) | — |
| user | read_all | read, create, update, delete (own) | read_all | read, update, delete (own) | — |
| guest | read_all | — | read_all | — | — |

### Пример вывода

```bash
POST /api/v1/auth/login
{"email": "admin@example.com", "password": "AdminPass123!"}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Структура проекта

```text
app/
    main.py              # FastAPI-приложение, middleware, health
    core/
        config.py        # Settings (env-driven, pydantic-settings)
        security.py      # bcrypt, JWT encode/decode, TokenError
        rate_limiter.py  # SlowAPI + Redis limiter
        exceptions.py    # HTTPException-фабрики
    db/
        base.py          # SQLAlchemy Base
        session.py       # async engine, session factory
    api/
        deps.py          # get_current_user / get_current_user_optional
        routes/
            auth.py      # register, login, refresh, logout
            users.py     # me, update, delete
            admin.py     # roles, rules, assign
            mock_resources.py  # products, orders, shops
    services/
        auth_service.py      # регистрация, логин, refresh, logout
        user_service.py      # профиль, soft delete
        admin_service.py     # CRUD ролей и правил
        access_service.py    # RBAC-проверка
    repositories/
        base.py          # BaseRepository
        users.py         # UserRepository
        roles.py         # RoleRepository
        access_rules.py  # AccessRuleRepository
        refresh_tokens.py # RefreshTokenRepository
    models/              # SQLAlchemy: User, Role, BusinessElement, ...
    schemas/             # Pydantic DTO: Register, Login, TokenPair, ...
    seed/
        seed_data.py     # идемпотентное заполнение
alembic/                 # миграции
tests/
    unit/                # 193 теста (services, models, schemas)
    integration/         # API-тесты (требуют PostgreSQL)
docker-compose.yml       # PostgreSQL 16 + Redis 7 + backend
Makefile                 # команды разработки
pyproject.toml           # ruff config
Dockerfile
entrypoint.sh            # alembic upgrade head + seed + uvicorn
requirements.txt
requirements-test.txt
pytest.ini
.env.example
.env.docker.example
```

---

## Команды (Makefile)

```bash
make build             # docker compose up --build
make up / make down    # контейнеры в фоне / остановить
make migrate           # alembic upgrade head
make seed              # наполнить тестовыми данными

make lint              # ruff check + ruff format --check
make lint-fix          # ruff check --fix + ruff format
make format            # форматирование

make test              # unit-тесты (193)
make test-cov          # тесты + покрытие
```

Настройки линтеров — в `pyproject.toml` (Ruff).

---

## Планы по улучшению

- **Mypy** — статическая типизация для core-модулей.
- **Integration тесты в CI** — PostgreSQL service container, полный пайплайн.
- **Refresh token rotation** — при refresh старый JTI отзывается, новый выпускается.
- **Blacklist access-токенов** — короткий TTL (15 мин) смягчает, но logout не инвалидирует access.
- **PostgreSQL full-text search** по users для админ-панели.
- **Деплой** (gunicorn + nginx + healthcheck).

---

## Лицензия

Учебный pet-проект. MIT. См. [LICENSE](LICENSE).

