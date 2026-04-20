SHELL := /bin/bash
MISE := mise exec --

MODEL_DIR := $(abspath ./.cache/all-MiniLM-L6-v2)
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

.PHONY: all run clean

all: run

download-model:
	@echo ">>> ./examples/basic-usage: download-model"
	@for file in $(MODEL_FILES); do \
		target="$(MODEL_DIR)/$$file"; \
		mkdir -p "$$(dirname "$$target")"; \
		if [ ! -f "$$target" ]; then \
			echo ">>> downloading $$file"; \
			curl -L --fail "$(MODEL_BASE_URL)/$$file?download=true" -o "$$target"; \
		fi; \
	done

run: download-model
	@echo ">>> ./examples/benchmark-corpora: run"
	$(MISE) uv run --frozen python main.py

clean:
	@echo ">>> ./examples/benchmark-corpora: clean"
	find . -type d -name __pycache__ -prune -exec rm -rf {} +