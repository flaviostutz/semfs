SHELL := /bin/bash
MISE := mise exec --
ROOT_DIR := $(abspath ../..)
WHEEL_GLOB := $(ROOT_DIR)/lib/dist/*.whl
CERT_BUNDLE := $(shell $(ROOT_DIR)/.venv/bin/python -c 'import certifi; print(certifi.where())' 2>/dev/null)
CHROMA_MODEL_DIR := $(HOME)/.cache/chroma/onnx_models/all-MiniLM-L6-v2
CHROMA_MODEL_ARCHIVE := $(CHROMA_MODEL_DIR)/onnx.tar.gz
CHROMA_MODEL_URL := https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz
CHROMA_MODEL_SHA256 := 913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3
export UV_PROJECT_ENVIRONMENT := $(ROOT_DIR)/.venv
export UV_CACHE_DIR := $(ROOT_DIR)/.cache/uv

.PHONY: all run clean

all: run

run:
	@echo ">>> ./examples/benchmark-corpora: run"
	@ls $(WHEEL_GLOB) >/dev/null 2>&1 || { echo "Build artifacts missing. Run 'make build' first."; exit 1; }
	$(MISE) uv sync --project . --frozen
	$(MISE) uv pip install --python "$(UV_PROJECT_ENVIRONMENT)/bin/python" --force-reinstall $(WHEEL_GLOB)
	@mkdir -p "$(CHROMA_MODEL_DIR)"
	@if [ ! -f "$(CHROMA_MODEL_DIR)/onnx/model.onnx" ]; then \
		echo ">>> prewarming Chroma ONNX model cache"; \
		if [ ! -f "$(CHROMA_MODEL_ARCHIVE)" ] || [ "$$(shasum -a 256 "$(CHROMA_MODEL_ARCHIVE)" | awk '{print $$1}')" != "$(CHROMA_MODEL_SHA256)" ]; then \
			curl -Lk "$(CHROMA_MODEL_URL)" -o "$(CHROMA_MODEL_ARCHIVE)"; \
		fi; \
		tar -xzf "$(CHROMA_MODEL_ARCHIVE)" -C "$(CHROMA_MODEL_DIR)"; \
	fi
	SSL_CERT_FILE="$(CERT_BUNDLE)" CURL_CA_BUNDLE="$(CERT_BUNDLE)" $(MISE) uv run --project . python main.py

clean:
	@echo ">>> ./examples/benchmark-corpora: clean"
	find . -type d -name __pycache__ -prune -exec rm -rf {} +