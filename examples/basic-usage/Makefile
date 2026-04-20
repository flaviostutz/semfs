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

.PHONY: all test-lib test-cli download-model clean

test: test-lib test-cli

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

test-lib: download-model
	@echo ">>> ./examples/basic-usage: run"
	$(MISE) uv run --project . python main.py

test-cli: download-model
	@echo ">>> ./examples/basic-usage: run-cli"
	@set -euo pipefail; \
	index_output="$$(mktemp)"; \
	chunk_output="$$(mktemp)"; \
	file_output="$$(mktemp)"; \
	trap 'rm -f "$$index_output" "$$chunk_output" "$$file_output"' EXIT; \
	\
	echo "BEGIN QUERY: HOW DO INSTALLERS RECOVER..."; \
	$(MISE) uv run --frozen semfs chunks sample-corpus 'how do installers recover an offline zigbee hub?' --top 5 --contents --verbose | tee "$$chunk_output"; \
	echo "END QUERY"; \
	grep -q 'devices/zigbee-hub-recovery.txt\[1:6\]' "$$chunk_output"; \
	grep -q 'Recovery sequence:' "$$chunk_output"; \
	\
	echo "BEGIN QUERY: STEPS TO PREPARE A TECHNICIAN..."; \
	$(MISE) uv run --frozen semfs files sample-corpus 'steps to prepare a technician visit for thermostat or lock issues' --top 5 --verbose | tee "$$file_output"; \
	echo "END QUERY"; \
	grep -qx 'support/field-visit-prep.md' "$$file_output"; \
	grep -qx 'devices/thermostat-onboarding.md' "$$file_output"; \
	\
	echo ">>> ./examples/basic-usage: run-cli assertions passed"

test-xdrs:
	$(MISE) uv run --frozen semfs chunks ../../.xdrs "how to test something?"

clean:
	@echo ">>> ./examples/basic-usage: clean"
	rm -rf .venv
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
