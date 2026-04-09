import logging
from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.health import check_database_health
from app.schemas.health import HealthCheck, ReadyCheck

router = APIRouter(tags=["health"])

STATUS_HEALTHY = "healthy"
STATUS_UNHEALTHY = "unhealthy"

LOGGER = logging.getLogger(__name__)


@router.get("/health", response_model=HealthCheck)
async def health() -> JSONResponse:
    """Basic health check to verify the application is up."""
    response = {
        "status": STATUS_HEALTHY,
        "environment": settings.ENVIRONMENT.value,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get("/ready", response_model=ReadyCheck)
async def ready(
    db: SessionDep,
) -> JSONResponse:
    """Readiness check to verify external dependencies (DB) are available."""
    database_status = await check_database_health(db=db)

    overall_status = STATUS_HEALTHY if database_status else STATUS_UNHEALTHY
    http_status = status.HTTP_200_OK if database_status else status.HTTP_503_SERVICE_UNAVAILABLE

    response = {
        "status": overall_status,
        "environment": settings.ENVIRONMENT.value,
        "version": settings.APP_VERSION,
        "app": STATUS_HEALTHY,
        "database": STATUS_HEALTHY if database_status else STATUS_UNHEALTHY,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    return JSONResponse(status_code=http_status, content=response)
