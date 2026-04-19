SHELL := /bin/bash
MISE := mise exec --
ROOT_DIR := $(abspath ../..)
WHEEL_GLOB := $(ROOT_DIR)/lib/dist/*.whl
export UV_PROJECT_ENVIRONMENT := $(ROOT_DIR)/.venv
export UV_CACHE_DIR := $(ROOT_DIR)/.cache/uv

.PHONY: all run clean

all: run

run:
	@echo ">>> ./examples/benchmark-corpora: run"
	@ls $(WHEEL_GLOB) >/dev/null 2>&1 || { echo "Build artifacts missing. Run 'make build' first."; exit 1; }
	$(MISE) uv sync --project . --frozen
	$(MISE) uv pip install --python "$(UV_PROJECT_ENVIRONMENT)/bin/python" --force-reinstall $(WHEEL_GLOB)
	HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 $(MISE) uv run --project . python main.py

clean:
	@echo ">>> ./examples/benchmark-corpora: clean"
	find . -type d -name __pycache__ -prune -exec rm -rf {} +