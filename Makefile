SHELL := /bin/bash
MISE := mise exec --
ROOT_DIR := $(abspath .)

.PHONY: all setup install build lint lint-fix test test-unit test-integration test-examples run dev update-lockfile clean bump download-model-minilm

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

# ---------------------------------------------------------------------------
# download-model-minilm: Manual fallback for fetching the all-MiniLM-L6-v2
# model files directly from HuggingFace using curl, without relying on the
# HuggingFace Python library or any network access from within Python.
#
# Use this when the HuggingFace Hub client cannot reach the internet at build
# or runtime — for example, due to SSL certificate issues, corporate proxy
# restrictions, or fully air-gapped environments — but you still need a local
# copy of the model to use via model.localPath in your .semfsrc.
#
# The downloaded files are placed in MODEL_DIR (default: .cache/all-MiniLM-L6-v2)
# and can be referenced with:
#   "model": { "localPath": "./.cache/all-MiniLM-L6-v2" }
#
# Usage:
#   make download-model-minilm
#   make download-model-minilm MODEL_DIR=/path/to/custom/dir
# ---------------------------------------------------------------------------
MODEL_DIR ?= $(ROOT_DIR)/.cache/all-MiniLM-L6-v2
MODEL_BASE_URL := https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main
MODEL_FILES := \
	1_Pooling/config.json \
	config.json \
	config_sentence_transformers.json \
	modules.json \
	model.safetensors \
	sentence_bert_config.json \
	special_tokens_map.json \
	tokenizer.json \
	tokenizer_config.json \
	vocab.txt

download-model-minilm:
	@echo ">>> .: download-model-minilm to $(MODEL_DIR)"
	@for file in $(MODEL_FILES); do \
		target="$(MODEL_DIR)/$$file"; \
		mkdir -p "$$(dirname "$$target")"; \
		if [ ! -f "$$target" ]; then \
			echo "  downloading $$file"; \
			curl -L --fail "$(MODEL_BASE_URL)/$$file?download=true" -o "$$target"; \
		else \
			echo "  skipping $$file (already present)"; \
		fi; \
	done
	@echo ">>> Model downloaded to $(MODEL_DIR)"
