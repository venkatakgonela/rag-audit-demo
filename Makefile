.DEFAULT_GOAL := help
.PHONY: help setup up down lint format typecheck test test-integration db-init run clean

help:
	@printf '%s\n' \
	  'setup             Install locked dependencies and create .env only if absent' \
	  'up                Start the synthetic database and wait for readiness' \
	  'down              Stop the database without deleting its volume' \
	  'lint              Check lint rules and formatting' \
	  'format            Format Python source and tests' \
	  'typecheck         Run basic static type checks' \
	  'test              Run unit tests with coverage (no Docker needed)' \
	  'test-integration  Run database tests (requires a running database)' \
	  'db-init           Enable vector using the shared tracked SQL file' \
	  'run               Serve the API on 127.0.0.1:8000' \
	  'clean             Remove generated Python artifacts, not .env or DB data' \
	  'help              Show these targets'

setup:
	uv sync --frozen
	@test -e .env || cp .env.example .env

up:
	docker compose up -d --wait

down:
	docker compose down

lint:
	uv run --frozen ruff check .
	uv run --frozen ruff format --check .

format:
	uv run --frozen ruff format .

typecheck:
	uv run --frozen mypy

test:
	uv run --frozen pytest -m "not integration" --cov --cov-report=term-missing

test-integration:
	uv run --frozen pytest --run-integration -m integration

db-init:
	uv run --frozen python -m rag_audit.db --init-sql docker/init/001-enable-vector.sql

run:
	uv run --frozen uvicorn rag_audit.api.main:app --host 127.0.0.1 --port 8000

clean:
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache htmlcov build dist
	rm -f .coverage .coverage.* coverage.xml
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
