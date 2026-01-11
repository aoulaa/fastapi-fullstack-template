from unittest.mock import AsyncMock, patch

import pytest
from arq.worker import Worker

from app.core.worker import shutdown, startup


@pytest.mark.asyncio
async def test_worker_startup():
    mock_ctx = AsyncMock(spec=Worker)
    with patch("app.core.worker.check_database_connection", new_callable=AsyncMock) as mock_check:
        await startup(mock_ctx)
        mock_check.assert_called_once()


@pytest.mark.asyncio
async def test_worker_shutdown():
    mock_ctx = AsyncMock(spec=Worker)
    # Check if it runs without error
    await shutdown(mock_ctx)
