.PHONY: install fmt lint type test test-integration test-migration check up down logs migrate

install:
	uv sync

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run mypy src

test:
	uv run pytest -m "not integration and not migration"

test-integration:
	uv run pytest -m integration

test-migration:
	uv run pytest -m migration
	uv run alembic upgrade head
	uv run alembic downgrade base
	uv run alembic upgrade head

# CLAUDE.md §7 order: unit -> integration -> migration -> lint/type.
# `check` runs the always-available subset (unit + lint + type); the
# integration/migration stages need `make up` first and are run explicitly.
check: test lint type

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

migrate:
	uv run alembic upgrade head
