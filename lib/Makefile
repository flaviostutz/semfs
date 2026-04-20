SHELL := /bin/bash
MISE := mise exec --
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
	@echo ">>> ./lib: install"
	$(MISE) uv sync --project . --frozen --all-extras --dev

build: install
	@echo ">>> ./lib: build"
	rm -rf dist
	$(MISE) uv build --project . --out-dir dist

lint: install
	@echo ">>> ./lib: lint"
	$(MISE) uv run --project . ruff format --check .
	$(MISE) uv run --project . ruff check .
	$(MISE) uv run --project . pyright
	$(MISE) uv run --project . pip-audit

lint-fix: install
	@echo ">>> ./lib: lint-fix"
	$(MISE) uv run --project . ruff format .
	$(MISE) uv run --project . ruff check . --fix
	$(MISE) uv run --project . pyright
	$(MISE) uv run --project . pip-audit

test: test-unit

test-unit: install
	@echo ">>> ./lib: test-unit"
	$(MISE) uv run --project . pytest tests -o cache_dir=.cache/pytest --cov=src/$(PACKAGE_NAME) --cov-branch --cov-report=term-missing --cov-fail-under=80

test-integration: install
	@echo ">>> ./lib: test-integration"
	$(MISE) uv run --project . pytest tests_integration -o cache_dir=.cache/pytest

run: install
	@echo ">>> ./lib: run"
	$(MISE) uv run --project . python -m $(PACKAGE_NAME) --help

dev:
	@echo ">>> ./lib: dev"
	$(MISE) uv run --project . python -m $(PACKAGE_NAME) index ../.venv/ --verbose

update-lockfile:
	@echo ">>> ./lib: update-lockfile"
	$(MISE) uv lock --project . --upgrade

clean:
	@echo ">>> ./lib: clean"
	rm -rf dist .cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

publish: build
	@echo ">>> ./lib: publish"
	$(MISE) uv publish --project .