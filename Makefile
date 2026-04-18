SHELL := /bin/bash

PACKAGE_NAME ?= semfs

.PHONY: all install build lint lint-fix test test-unit test-examples run dev update-lockfile clean bump

all: build lint test

install:
	uv sync --frozen --all-extras --dev

build: install
	uv build

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright
	uv run pip-audit

lint-fix:
	uv run ruff format .
	uv run ruff check . --fix
	uv run pyright
	uv run pip-audit

test: test-unit test-examples

test-unit:
	uv run pytest --cov=src/$(PACKAGE_NAME) --cov-branch --cov-report=term-missing --cov-fail-under=80

test-examples:
	@if [ -d examples ]; then $(MAKE) -C examples test PACKAGE_NAME=$(PACKAGE_NAME); else echo "No examples/ directory. Skipping"; fi

run:
	uv run python -m $(PACKAGE_NAME) --help

dev: run

update-lockfile:
	uv lock --upgrade

clean:
	rm -rf .venv dist build .pytest_cache .ruff_cache .coverage htmlcov benchmarks
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

bump:
	# 	npx -y agentme@latest
	npx -y filedist@latest --packages git:github.com/flaviostutz/agentme.git
