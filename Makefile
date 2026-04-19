SHELL := /bin/bash
ROOT_DIR := $(abspath .)
export UV_PROJECT_ENVIRONMENT := $(ROOT_DIR)/.venv
export UV_CACHE_DIR := $(ROOT_DIR)/.cache/uv

.PHONY: setup all install build lint lint-fix test test-unit test-integration test-examples run dev update-lockfile clean bump

setup: install

all: build lint test

install:
	$(MAKE) -C lib install

build:
	$(MAKE) -C lib build

lint:
	$(MAKE) -C lib lint

lint-fix:
	$(MAKE) -C lib lint-fix

test: test-unit test-integration test-examples

test-unit:
	$(MAKE) -C lib test-unit

test-integration:
	$(MAKE) -C lib test-integration

test-examples: build
	@for dir in examples/*; do \
		if [ -f "$$dir/pyproject.toml" ]; then \
			echo ">>> Running $$dir"; \
			UV_PROJECT_ENVIRONMENT="$(UV_PROJECT_ENVIRONMENT)" UV_CACHE_DIR="$(UV_CACHE_DIR)" uv sync --project "$$dir" --frozen || exit 1; \
			UV_PROJECT_ENVIRONMENT="$(UV_PROJECT_ENVIRONMENT)" UV_CACHE_DIR="$(UV_CACHE_DIR)" uv pip install --python "$(UV_PROJECT_ENVIRONMENT)/bin/python" --force-reinstall lib/dist/*.whl || exit 1; \
			HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 UV_PROJECT_ENVIRONMENT="$(UV_PROJECT_ENVIRONMENT)" UV_CACHE_DIR="$(UV_CACHE_DIR)" uv run --project "$$dir" python "$$dir/main.py" || exit 1; \
		fi; \
	done

run:
	$(MAKE) -C lib run

dev: run

update-lockfile:
	$(MAKE) -C lib update-lockfile

clean:
	$(MAKE) -C lib clean
	rm -rf .cache .venv
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

bump:
	# 	npx -y agentme@latest
	npx -y filedist@latest --packages git:github.com/flaviostutz/agentme.git
