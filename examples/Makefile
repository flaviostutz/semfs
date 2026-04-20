SHELL := /bin/bash

.PHONY: all run run-benchmark download-model clean

all: run

test:
	@echo ">>> ./examples/basic-usage: test"
	$(MAKE) -C basic-usage test

run-benchmark:
	@echo ">>> ./examples/benchmark-corpora: run"
	$(MAKE) -C benchmark-corpora run

download-model:
	@echo ">>> ./examples/basic-usage: download-model"
	$(MAKE) -C basic-usage download-model

clean:
	@echo ">>> .: clean examples"
	@echo ">>> ./examples/basic-usage: clean"
	$(MAKE) -C basic-usage clean
	@echo ">>> ./examples/benchmark-corpora: clean"
	$(MAKE) -C benchmark-corpora clean