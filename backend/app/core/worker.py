import asyncio
import logging

import uvloop
from arq.connections import RedisSettings
from arq.worker import Worker

from app.core.setup import check_database_connection
from app.tasks import all_tasks

from .config import settings

# Set up uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def startup(ctx: Worker) -> None:
    logger.info("Worker Started")
    await check_database_connection()


async def shutdown(ctx: Worker) -> None:
    logger.info("Worker Stopped")


class WorkerSettings:
    """
    Configuration for the arq worker.
    """

    functions = all_tasks
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
