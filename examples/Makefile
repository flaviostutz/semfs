SHELL := /bin/bash

.PHONY: all run clean

all: run

run:
	@echo ">>> ./examples/basic-usage: run"
	$(MAKE) -C basic-usage run

run-benchmark:
	@echo ">>> ./examples/benchmark-corpora: run"
	$(MAKE) -C benchmark-corpora run

clean:
	@echo ">>> .: clean examples"
	@echo ">>> ./examples/basic-usage: clean"
	$(MAKE) -C basic-usage clean
	@echo ">>> ./examples/benchmark-corpora: clean"
	$(MAKE) -C benchmark-corpora clean