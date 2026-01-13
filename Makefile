
# Variables
PYTHON := backend/.venv/bin/python
export PYTHONPATH := backend
APP_MODULE := app.main:app
WORKER_SETTINGS := app.core.worker.WorkerSettings

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Run initial setup (install, env, migrations, pre-commit)
	./scripts/setup.sh
	@make install-hooks

.PHONY: install-hooks
install-hooks: ## Install git hooks (pre-commit)
	uv --project backend run pre-commit install

.PHONY: install
install: ## Install dependencies using uv
	uv --project backend sync

.PHONY: run
run: ## Run the FastAPI application locally with reload
	uv --project backend run uvicorn app.main:app --reload

.PHONY: worker
worker: ## Run the ARQ background worker
	uv --project backend run arq $(WORKER_SETTINGS)

.PHONY: test
test: ## Run tests using pytest
	uv --project backend run pytest

.PHONY: test-frontend
test-frontend: ## Run frontend Playwright tests
	cd frontend && npx playwright test

.PHONY: test-frontend-ui
test-frontend-ui: ## Run frontend tests with Playwright UI
	cd frontend && npx playwright test --ui

.PHONY: test-frontend-headed
test-frontend-headed: ## Run frontend tests with visible browser
	cd frontend && npx playwright test --headed

.PHONY: test-frontend-debug
test-frontend-debug: ## Run frontend tests in debug mode
	cd frontend && npx playwright test --debug

.PHONY: test-all
test-all: ## Run all tests (backend + frontend)
	@echo "Running backend tests..."
	@make test
	@echo "\nRunning frontend tests..."
	@make test-frontend

.PHONY: lint
lint: ## Run linting checks (ruff and mypy)
	uv --project backend run ruff check .
	cd backend && uv run mypy app

.PHONY: format
format: ## Run code formatting (ruff)
	uv --project backend run ruff format .
	uv --project backend run ruff check . --fix

.PHONY: migrate
migrate: ## Run database migrations to head
	cd backend && uv run alembic upgrade head

.PHONY: makemigrations
makemigrations: ## Create a new database migration (usage: make makemigrations m="migration message")
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

.PHONY: cmd
cmd: ## Run a custom command from app.commands (usage: make cmd n="command_name")
	cd backend && uv run python -m app.commands.$(n)

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

.PHONY: generate-client
generate-client: ## Generate the frontend client from the backend OpenAPI spec
	./scripts/generate-client.sh
