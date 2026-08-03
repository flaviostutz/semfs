SHELL := /bin/bash
MISE := mise exec --

.PHONY: all run clean

all: run

run:
	@echo ">>> ./examples/benchmark-corpora: run"
	$(MISE) uv run --frozen python main.py

clean:
	@echo ">>> ./examples/benchmark-corpora: clean"
	find . -type d -name __pycache__ -prune -exec rm -rf {} +