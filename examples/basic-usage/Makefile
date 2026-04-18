ifeq ($(CI),)
MISE_DISABLE_TOOLS ?= python,uv,node
endif

MISE := MISE_DISABLE_TOOLS=$(MISE_DISABLE_TOOLS) mise exec --

run:
	$(MISE) uv run python main.py
