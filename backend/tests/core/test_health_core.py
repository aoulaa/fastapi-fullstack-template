from unittest.mock import AsyncMock, patch

import pytest

from app.core.health import check_database_health


@pytest.mark.asyncio
async def test_check_database_health_success(db):
    # db is an AsyncSession
    # Mocking db.execute to succeed
    with patch.object(db, "execute", new_callable=AsyncMock) as mock_execute:
        result = await check_database_health(db)
        assert result is True
        mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_check_database_health_failure(db):
    with patch.object(db, "execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("DB Error")
        result = await check_database_health(db)
        assert result is False
