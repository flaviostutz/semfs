SHELL := /bin/bash
ROOT_DIR := $(abspath ..)
export UV_PROJECT_ENVIRONMENT := $(ROOT_DIR)/.venv
export UV_CACHE_DIR := $(ROOT_DIR)/.cache/uv
export RUFF_CACHE_DIR := $(abspath .cache/ruff)
export PYTHONPYCACHEPREFIX := $(abspath .cache/pycache)
export COVERAGE_FILE := $(abspath .cache/coverage)

PACKAGE_NAME ?= semfs

.PHONY: all install build lint lint-fix test test-unit test-integration run dev update-lockfile clean publish

all: build lint test

install:
	uv sync --project . --frozen --all-extras --dev

build: install
	rm -rf dist
	uv build --project . --out-dir dist

lint: install
	uv run --project . ruff format --check .
	uv run --project . ruff check .
	uv run --project . pyright
	uv run --project . pip-audit

lint-fix: install
	uv run --project . ruff format .
	uv run --project . ruff check . --fix
	uv run --project . pyright
	uv run --project . pip-audit

test: test-unit test-integration

test-unit: install
	uv run --project . pytest tests -o cache_dir=.cache/pytest --cov=src/$(PACKAGE_NAME) --cov-branch --cov-report=term-missing --cov-report=html:.cache/htmlcov --cov-fail-under=80

test-integration: install
	uv run --project . pytest tests_integration -o cache_dir=.cache/pytest

run: install
	uv run --project . python -m $(PACKAGE_NAME) --help

dev: run

update-lockfile:
	uv lock --project . --upgrade

clean:
	rm -rf dist .cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

publish: build
	uv publish --project .