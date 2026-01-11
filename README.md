# FastAPI Fullstack Boilerplate

A modern, production-ready fullstack boilerplate featuring FastAPI, PostgreSQL, and Redis.

## 🚀 Features

- **FastAPI**: Modern, high-performance Python web framework.
- **PostgreSQL**: Robust relational database with **SQLAlchemy 2.0** and **Alembic** migrations.
- **Redis**: High-speed caching, rate limiting, and background task queueing (ARQ).
- **Authentication**: Secure JWT-based authentication with password hashing (bcrypt).
- **CI/CD**: Pre-configured GitHub Actions for linting (Ruff), type checking (Mypy), and testing (Pytest).
- **Developer Experience**:
  - `uv` for lightning-fast dependency management.
  - `Makefile` for common development tasks.
  - Fully Dockerized with `docker-compose`.
  - VS Code pre-configured for auto-formatting and debugging.

## 🛠 Quick Start

### 1. Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Docker & Docker Compose (optional)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/FastAPI-Fullstack-Boilerplate.git
cd FastAPI-Fullstack-Boilerplate

# Copy environment variables
cp .env.example .env

# Setup environment (using Makefile)
make install
```

### 3. Running Locally

#### Option A: Direct (Fastest)

```bash
# Run the FastAPI server
make run

# Run tests
make test
```

#### Option B: Docker (Closest to Production)

For local development with Docker (includes hot-reloading):

```bash
docker-compose -f docker-compose.local.yml up --build
```

## 📂 Project Structure

```text
├── .github/          # CI/CD Workflows
├── .vscode/          # Editor settings & Debugger config
├── backend/          # FastAPI application
│   ├── app/          # Core logic (API, Models, Schemas, Services)
│   ├── tests/        # Pytest test suite
│   ├── Dockerfile    # Backend container definition
│   └── pyproject.toml # Dependencies managed by 'uv'
├── Makefile          # Automation commands
└── docker-compose.yml # Local development infrastructure
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
