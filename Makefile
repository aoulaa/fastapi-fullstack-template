
# Variables
PYTHON := backend/.venv/bin/python
export PYTHONPATH := backend
APP_MODULE := app.main:app
WORKER_SETTINGS := app.core.worker.WorkerSettings

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Run initial setup (install, env, migrations, superuser)
	./scripts/setup.sh

.PHONY: install
install: ## Install dependencies using uv
	uv --project backend sync

.PHONY: run
run: ## Run the FastAPI application locally with reload
	$(PYTHON) -m uvicorn app.main:app --reload

.PHONY: worker
worker: ## Run the ARQ background worker
	$(PYTHON) -m arq $(WORKER_SETTINGS)

.PHONY: test
test: ## Run tests using pytest
	$(PYTHON) -m pytest

.PHONY: lint
lint: ## Run linting checks (ruff and mypy)
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy backend/app

.PHONY: format
format: ## Run code formatting (ruff)
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check . --fix

.PHONY: migrate
migrate: ## Run database migrations to head
	$(PYTHON) -m alembic upgrade head

.PHONY: makemigrations
makemigrations: ## Create a new database migration (usage: make makemigrations m="migration message")
	$(PYTHON) -m alembic revision --autogenerate -m "$(m)"


.PHONY: cmd
cmd: ## Run a custom command from app.commands (usage: make cmd n="command_name")
	$(PYTHON) -m app.commands.$(n)

.PHONY: docker-local
docker-local: ## Start local development services
	docker compose -f docker-compose.local.yml up -d

.PHONY: docker-prod
docker-prod: ## Start production services
	docker compose -f docker-compose.yml up -d

.PHONY: docker-down
docker-down: ## Stop all services
	docker compose -f docker-compose.local.yml down
	docker compose -f docker-compose.yml down

.PHONY: docker-logs
docker-logs: ## View docker compose logs
	docker compose logs -f

.PHONY: clean
clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
