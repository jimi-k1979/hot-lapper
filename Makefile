.PHONY: check lint test fmt

check: lint test

lint:
	uv run ruff check
	uv run ruff format --check
	uv run mypy
	uv run lint-imports

test:
	uv run pytest

fmt:
	uv run ruff check --fix
	uv run ruff format
