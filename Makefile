.PHONY: help install install-dev lint typecheck test test-cov build clean run-dry run all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	pip install .

install-dev: ## Install with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

lint: ## Run ruff linter and formatter check
	ruff check .
	ruff format --check .

lint-fix: ## Auto-fix lint issues
	ruff check --fix .
	ruff format .

typecheck: ## Run pyright type checker (strict mode)
	pyright .

test: ## Run all tests
	pytest tools/ tests/ -v

test-cov: ## Run tests with coverage report
	pytest tools/ tests/ -v --cov=tools --cov-report=term --cov-report=html

build: ## Build distribution packages
	python -m build

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ *.egg-info/ .mypy_cache/ .pytest_cache/ .ruff_cache/ .pyright_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

run-dry: ## Run knowledge pipeline in dry-run mode
	python tools/knowledge_updater.py --dry-run --log-level DEBUG

run: ## Run knowledge pipeline (writes to brain file)
	python tools/knowledge_updater.py --log-level INFO

run-news: ## Run news-only pipeline
	python tools/knowledge_updater.py --news-only --log-level INFO

validate: ## Run project structural validator
	python tools/run_test_scenarios.py

all: lint typecheck test-cov validate ## Run all checks (lint + typecheck + tests + validate)
