.PHONY: help build up down down-v restart logs
.PHONY: migrate seed
.PHONY: lint lint-fix format test test-cov

# ========================================
# DOCKER COMMANDS
# ========================================

build:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

down-v:
	docker compose down -v

restart: down up

logs:
	docker compose logs -f

# ========================================
# ALEMBIC (run via docker compose exec)
# ========================================

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.seed.seed_data

# ========================================
# LINTING & CODE QUALITY (ruff)
# ========================================

lint:
	ruff check .
	ruff format --check .

lint-fix:
	ruff check --fix .
	ruff format .

format:
	ruff check --fix .
	ruff format .

# ========================================
# TESTS
# ========================================

test:
	pytest tests/unit/ -q

test-cov:
	pytest tests/unit/ --cov=app --cov-report=term-missing -q

# ========================================
# HELP (default)
# ========================================

help:
	@echo Available commands:
	@echo.
	@echo DOCKER:
	@echo   build          Build and run containers
	@echo   up             Run containers in background
	@echo   down           Stop containers
	@echo   down-v         Stop containers and remove volumes
	@echo   restart        Restart containers
	@echo   logs           Show container logs
	@echo.
	@echo ALEMBIC:
	@echo   migrate        Apply migrations
	@echo   seed           Run seed data
	@echo.
	@echo LINTING:
	@echo   lint           Run ruff check + format check
	@echo   lint-fix       Auto-fix errors
	@echo   format         Format all code
	@echo.
	@echo TESTS:
	@echo   test           Run unit tests
	@echo   test-cov       Run unit tests with coverage

.DEFAULT_GOAL := help
