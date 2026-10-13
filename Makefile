.DEFAULT_GOAL := help

UV ?= uv
UV_RUN = $(UV) run --locked
UV_DEV_RUN = $(UV_RUN) --extra dev

.PHONY: help sync test format format-check lint check build manual-ui

help: ## Show available development commands
	@printf "Usage: make <target>\n\n"
	@awk -F '## ' '/^[[:alnum:]_-]+:.*## / { split($$1, target, ":"); printf "  %-14s %s\n", target[1], $$2 }' $(MAKEFILE_LIST)

sync: ## Install the project and development tools from uv.lock
	$(UV) sync --locked --extra dev

test: ## Run the unit tests
	$(UV_RUN) python -m unittest discover -s tests -v

format: ## Format Python source and tests with Black
	$(UV_DEV_RUN) python -m black src tests tools

format-check: ## Check Python formatting without changing files
	$(UV_DEV_RUN) python -m black --check src tests tools

lint: ## Run Flake8 on source and tests
	$(UV_DEV_RUN) python -m flake8 src tests tools --max-line-length=88

check: format-check lint test ## Run formatting, lint, and unit tests

build: ## Build the Python distribution
	$(UV) build

manual-ui: ## Launch the manual-only browser test helper
	PYTHONPATH=src $(UV_RUN) python tools/manual_web.py

