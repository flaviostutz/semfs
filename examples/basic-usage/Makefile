SHELL := /bin/bash
MISE := mise exec --

.PHONY: all test-lib test-cli clean

test: test-lib test-cli

test-lib:
	@echo ">>> ./examples/basic-usage: run"
	$(MISE) uv run --project . python main.py

test-cli:
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
