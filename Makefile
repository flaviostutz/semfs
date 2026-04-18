SHELL := /bin/bash

PACKAGE_NAME ?= semfs
ifeq ($(CI),)
MISE_DISABLE_TOOLS ?= python,uv,node
endif

MISE := MISE_DISABLE_TOOLS=$(MISE_DISABLE_TOOLS) mise exec --
PYTHON := $(MISE) python

.DEFAULT_GOAL := all

.PHONY: all setup install compile package build lint lint-fix test test-unit test-examples test-integration clean run dev update-lockfile docgen publish release bump

all: build lint test

setup:
	@if [ -n "$(MISE_DISABLE_TOOLS)" ]; then \
		echo "Using system Python/uv/node through mise for local development"; \
	else \
		mise install; \
	fi

install:
	$(MISE) uv sync --all-extras --dev

compile: install
	$(PYTHON) -m compileall src

package: install
	$(MISE) uv build

build: install compile package

lint:
	$(MISE) uv run ruff format --check .
	$(MISE) uv run ruff check .
	$(MISE) uv run pyright
	$(MISE) uv run pip-audit

lint-fix:
	$(MISE) uv run ruff format .
	$(MISE) uv run ruff check . --fix
	$(MISE) uv run pyright
	$(MISE) uv run pip-audit

test: test-unit test-examples

test-unit:
	$(MISE) uv run pytest --cov=src/$(PACKAGE_NAME) --cov-branch --cov-report=term-missing --cov-fail-under=80 tests

test-examples:
	$(MAKE) -C examples test PACKAGE_NAME=$(PACKAGE_NAME)

test-integration:
	$(MISE) uv run pytest tests_integration

run:
	$(MISE) uv run semfs --help

dev: run

update-lockfile:
	$(MISE) uv lock --upgrade

docgen:
	@echo "README and XDR documents are maintained as source files."

publish: build lint test
	$(MISE) uv publish

release:
	npx -y monotag@latest tag

clean:
	rm -rf .venv dist build .pytest_cache .ruff_cache .coverage htmlcov .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

bump:
	# npx -y agentme@latest
	npx -y filedist@latest --packages git:github.com/flaviostutz/agentme.git
