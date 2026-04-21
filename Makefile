SHELL := /bin/bash
MISE := mise exec --
ROOT_DIR := $(abspath .)

.PHONY: all setup install build lint lint-fix test test-unit test-integration test-examples run dev update-lockfile clean bump

all: build lint test

setup:
	@echo ">>> .: setup"
	mise install
	$(MAKE) install

install:
	@echo ">>> ./lib: install"
	$(MAKE) -C lib install

build:
	@echo ">>> ./lib: build"
	$(MAKE) -C lib build

lint:
	@echo ">>> ./lib: lint"
	$(MAKE) -C lib lint

lint-fix:
	@echo ">>> ./lib: lint-fix"
	$(MAKE) -C lib lint-fix

test: test-unit test-examples

test-unit:
	@echo ">>> ./lib: test-unit"
	$(MAKE) -C lib test-unit

test-integration:
	@echo ">>> ./lib: test-integration"
	$(MAKE) -C lib test-integration

test-examples: build
	@echo ">>> ./examples: test"
	$(MAKE) -C examples test

run:
	@echo ">>> ./lib: run"
	$(MAKE) -C lib run

run-benchmark:
	@echo ">>> ./examples: run-benchmark"
	$(MAKE) -C examples run-benchmark

dev: run

update-lockfile:
	@echo ">>> ./lib: update-lockfile"
	$(MAKE) -C lib update-lockfile

clean:
	@echo ">>> .: clean"
	@echo ">>> ./examples: clean"
	$(MAKE) -C examples clean
	@echo ">>> ./lib: clean"
	$(MAKE) -C lib clean
	rm -rf .cache .venv
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

bump:
	@echo ">>> .: bump"
	$(MISE) npx -y agentme@latest 
# 	$(MISE) npx -y filedist@latest --packages git:github.com/flaviostutz/agentme.git
