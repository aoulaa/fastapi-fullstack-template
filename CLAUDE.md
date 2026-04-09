# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands are available via `make`. Run `make help` or inspect the `Makefile` for the full list.

### Development

```bash
make setup              # Full project setup (deps, .env, migrations, pre-commit hooks)
make run-backend        # Run FastAPI backend with hot-reload (localhost:8000)
make run-frontend       # Run React frontend development server (localhost:5173)
make worker             # Run ARQ background worker
make docker-local       # Start all local services (PostgreSQL, Redis, FastAPI, frontend)
```

### Testing

```bash
make test               # Backend: pytest
make frontend-test      # Frontend: Playwright E2E
make test-all           # Both backend and frontend tests
# Run a single pytest test:
cd backend && uv run pytest tests/path/to/test_file.py::test_function -v
```

### Linting & Formatting

```bash
make lint               # Ruff check + Mypy type checking
make format             # Ruff format + auto-fix
```

### Database

```bash
make migrate                        # Apply Alembic migrations to head
make makemigrations m="description" # Generate a new migration from model changes
```

### Client Generation

```bash
make frontend-gen       # Regenerate frontend TypeScript client from backend OpenAPI spec
```

Run this whenever backend API schemas or routes change. The generated files are in `frontend/src/client/`.

## Architecture

### Overview

This is a fullstack boilerplate: async FastAPI backend + React frontend, connected via an auto-generated OpenAPI TypeScript client.

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL, with Redis for background jobs (ARQ) and rate limiting
- **Frontend**: React 19 + TanStack Router (file-based) + TanStack Query + Tailwind CSS + Radix UI
- **Reverse proxy**: Nginx (production only)

### Backend Structure (`backend/app/`)

```
api/
  __init__.py       # Aggregates all routers under /api prefix
  deps.py           # Shared dependencies: SessionDep, CurrentUser, RedisDep
  routes/           # Versioned endpoints under /api/v1/
core/
  config.py         # All settings (Pydantic BaseSettings, reads from .env)
  db.py             # async_engine, local_session, async_get_db dependency
  security.py       # JWT creation/verification, bcrypt password hashing
  setup.py          # lifespan_factory, create_application
  worker.py         # ARQ worker configuration
  utils/
    cache.py        # Redis client initialization
    queue.py        # ARQ job queue pool
    rate_limit.py   # Redis-based rate limiting
models/
  base.py           # BaseModel with IDMixin, TimestampMixin, SoftDeleteMixin
  user.py, item.py  # SQLAlchemy ORM models
schemas/            # Pydantic schemas (separate Create/Update/Read per resource)
crud/
  base.py           # Generic BaseCRUD[ModelType] with get/get_multi/create/update/delete
  users.py, items.py
tasks/              # ARQ async background task definitions
commands/           # CLI scripts (e.g., create_first_superuser.py)
migrations/         # Alembic migrations
```

**Key pattern — BaseCRUD**: All resources use the generic `BaseCRUD[ModelType]` from `crud/base.py`. It provides `get()`, `get_multi()`, `create()`, `update()`, `delete()` (soft), `db_delete()` (hard), `exists()`, `count()`. Both `get` and `get_multi` accept SQLAlchemy loading options for eager loading.

**Soft deletes**: Models using `SoftDeleteMixin` set `is_deleted=True` and `deleted_at` on delete rather than removing rows.

### Frontend Structure (`frontend/src/`)

```
client/             # Auto-generated from OpenAPI (do not edit manually)
routes/             # TanStack Router file-based routes
  __root.tsx        # Root layout
  _layout.tsx       # Authenticated layout (redirects to /login if unauthenticated)
  login.tsx
  _layout/
    index.tsx       # Dashboard
    items.tsx
    settings.tsx
    admin.tsx
components/         # Reusable UI components (Radix UI-based)
hooks/              # Custom React hooks
lib/                # Utilities
```

### Authentication Flow

1. `POST /api/v1/login/access-token` — returns `{access_token}` in response body; sets HTTP-only refresh token cookie (7-day expiry)
2. Access token stored in localStorage; sent as `Authorization: Bearer <token>` on every request
3. On 401, frontend calls `POST /api/v1/login/refresh` using the refresh cookie
4. If refresh also fails, localStorage is cleared and user is redirected to `/login`
5. `POST /api/v1/logout` clears the refresh cookie server-side

JWT payload: `{sub: username_or_email, exp: ..., token_type: "access" | "refresh"}`

### API → Frontend Type Safety

The frontend TypeScript client (`frontend/src/client/`) is fully auto-generated from the backend's OpenAPI schema. After changing any backend schema, route, or response model, run `make generate-client` to keep the frontend in sync.

### Environment Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable                          | Purpose                                    |
| --------------------------------- | ------------------------------------------ |
| `SECRET_KEY`                    | JWT signing key (`openssl rand -hex 32`) |
| `POSTGRES_*`                    | Database connection                        |
| `REDIS_HOST/PORT`               | Redis connection                           |
| `ENABLE_REDIS_QUEUE`            | Toggle ARQ background jobs                 |
| `ENABLE_REDIS_RATE_LIMIT`       | Toggle rate limiting                       |
| `ADMIN_EMAIL/USERNAME/PASSWORD` | Initial superuser (created on startup)     |
| `VITE_API_URL`                  | Frontend API base URL                      |

For Docker local dev, set `POSTGRES_SERVER=db` and `REDIS_HOST=redis`.
