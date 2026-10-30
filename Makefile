PYTHON ?= python3
VENV   := default_venv
BIN    := $(VENV)/bin

.DEFAULT_GOAL := help
.PHONY: help venv install update test tests lint format sample-db clean

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip

venv: $(BIN)/python ## Create the default_venv virtual environment

install: venv ## Install the pinned packages from requirements.txt
	$(BIN)/pip install -r requirements.txt

update: venv ## Upgrade packages in requirements.in and re-pin requirements.txt
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install --upgrade -r requirements.in
	$(BIN)/pip freeze > requirements.txt

test: ## Run the test suite
	$(BIN)/pytest

tests: test ## Same as make test

lint: ## Check code with ruff
	$(BIN)/ruff check .

format: ## Format code with ruff
	$(BIN)/ruff format .

sample-db: ## Build the sample SQLite database at data/sample.db
	$(BIN)/python -m interview_sandbox.sample_db

clean: ## Delete caches (keeps the venv)
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -not -path './$(VENV)/*' -prune -exec rm -rf {} +
