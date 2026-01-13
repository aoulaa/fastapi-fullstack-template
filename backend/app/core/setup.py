import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import anyio
import fastapi
from arq import create_pool
from arq.connections import RedisSettings as ArqRedisSettings
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text

from app.api.deps import get_current_superuser
from app.core.utils.rate_limit import rate_limiter
from app.models import *  # noqa: F403

from .config import (
    AppSettings,
    CORSSettings,
    DatabaseSettings,
    DefaultRateLimitSettings,
    EnvironmentOption,
    EnvironmentSettings,
    RedisSettings,
    settings,
)
from .db import async_engine as engine
from .utils import cache, queue


# -------------- database --------------
async def check_database_connection() -> None:
    max_retries = 5
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logging.info(
                "Database connection successful to %s:%s/%s",
                settings.POSTGRES_SERVER,
                settings.POSTGRES_PORT,
                settings.POSTGRES_DB,
            )
            return
        except (asyncio.CancelledError, KeyboardInterrupt):
            logging.info("Database connection check cancelled by user.")
            raise
        except Exception as e:
            if attempt == max_retries:
                logging.error(
                    "Database connection failed after %s attempts to %s: %s",
                    max_retries,
                    settings.POSTGRES_SERVER,
                    e,
                )
                raise e
            logging.warning(
                "Database connection attempt %s failed for %s. Retrying in %s seconds...",
                attempt,
                settings.POSTGRES_SERVER,
                retry_delay,
            )
            await anyio.sleep(retry_delay)


async def check_redis_connection() -> None:
    max_retries = 5
    retry_delay = 2

    checks = []
    if cache.client is not None:
        checks.append(("Cache", cache.client))
    if queue.pool is not None:
        checks.append(("Queue", queue.pool))
    if rate_limiter.client is not None:
        checks.append(("RateLimit", rate_limiter.client))

    if not checks:
        logging.info("Redis is disabled (no features enabled), skipping connection check.")
        return

    for attempt in range(1, max_retries + 1):
        try:
            for name, connection in checks:
                await connection.ping()
            logging.info(
                "Redis connection successful to %s:%s (Verified: %s)",
                settings.REDIS_HOST,
                settings.REDIS_PORT,
                ", ".join([c[0] for c in checks]),
            )
            return
        except (asyncio.CancelledError, KeyboardInterrupt):
            logging.info("Redis connection check cancelled by user.")
            raise
        except Exception as e:
            if attempt == max_retries:
                logging.error(
                    "Redis connection failed after %s attempts to %s: %s",
                    max_retries,
                    settings.REDIS_HOST,
                    e,
                )
                raise e
            logging.warning(
                "Redis connection attempt %s failed for %s. Retrying in %s seconds...",
                attempt,
                settings.REDIS_HOST,
                retry_delay,
            )
            await anyio.sleep(retry_delay)


# -------------- Redis Initialization --------------
# Note: If you want to use independent Redis instances for Cache, Queue, or
# Rate Limiting, simply create separate connection pools below using
# different URLs from your settings.


# -------------- queue --------------
async def create_redis_queue_pool() -> None:
    queue.pool = await create_pool(ArqRedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT))


async def close_redis_queue_pool() -> None:
    if queue.pool is not None:
        await queue.pool.aclose()  # type: ignore


# -------------- rate limit --------------
async def create_redis_rate_limit_pool() -> None:
    rate_limiter.initialize(settings.REDIS_URL)  # type: ignore


async def close_redis_rate_limit_pool() -> None:
    if rate_limiter.client is not None:
        await rate_limiter.client.aclose()  # type: ignore


# -------------- application --------------
async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


def lifespan_factory(
    settings: (
        DatabaseSettings | RedisSettings | AppSettings | CORSSettings | DefaultRateLimitSettings | EnvironmentSettings
    ),
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for a FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        await set_threadpool_tokens()

        try:
            if isinstance(settings, RedisSettings):
                any_redis_enabled = any(
                    [
                        settings.ENABLE_REDIS_QUEUE,
                        settings.ENABLE_REDIS_RATE_LIMIT,
                    ]
                )
                if any_redis_enabled:
                    if settings.ENABLE_REDIS_QUEUE:
                        await create_redis_queue_pool()
                    if settings.ENABLE_REDIS_RATE_LIMIT:
                        await create_redis_rate_limit_pool()

                    await check_redis_connection()

            if isinstance(settings, DatabaseSettings):
                await check_database_connection()

            initialization_complete.set()

            yield

        finally:
            if isinstance(settings, RedisSettings):
                if settings.ENABLE_REDIS_QUEUE:
                    await close_redis_queue_pool()
                if settings.ENABLE_REDIS_RATE_LIMIT:
                    await close_redis_rate_limit_pool()

    return lifespan


# -------------- application --------------
def create_application(
    router: APIRouter,
    settings: (
        DatabaseSettings | RedisSettings | AppSettings | CORSSettings | DefaultRateLimitSettings | EnvironmentSettings
    ),
    lifespan: Callable[[FastAPI], _AsyncGeneratorContextManager[Any]] | None = None,
    **kwargs: Any,
) -> FastAPI:
    """Creates and configures a FastAPI application based on the provided settings."""
    # --- before creating application ---
    if isinstance(settings, AppSettings):
        to_update = {
            "title": settings.APP_NAME,
            "description": settings.APP_DESCRIPTION,
            "contact": {"name": settings.CONTACT_NAME, "email": settings.CONTACT_EMAIL},
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    # Use custom lifespan if provided, otherwise use default factory
    if lifespan is None:
        lifespan = lifespan_factory(settings)

    application = FastAPI(lifespan=lifespan, **kwargs)
    application.include_router(router)

    if isinstance(settings, CORSSettings):
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
        )

    if isinstance(settings, EnvironmentSettings):
        if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
            docs_router = APIRouter()
            if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> dict[str, Any]:
                out: dict = get_openapi(title=application.title, version=application.version, routes=application.routes)
                return out

            application.include_router(docs_router)

    return application
