from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
def mock_queue_pool():
    mock_pool = AsyncMock()
    mock_job = AsyncMock()
    mock_job.job_id = "test_job_id"
    mock_pool.enqueue_job.return_value = mock_job

    with patch("app.core.utils.queue.pool", mock_pool):
        yield mock_pool


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, mock_queue_pool, normal_user_token_headers):
    response = await client.post("/api/v1/tasks/task", params={"message": "hello"}, headers=normal_user_token_headers)
    assert response.status_code == 201
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, mock_queue_pool, normal_user_token_headers):
    # Mocking ArqJob in the router module
    with patch("app.api.routes.tasks.ArqJob") as MockArqJob:
        mock_job_instance = AsyncMock()

        # Create a class to mock job info that has __dict__ or is a simple object
        class JobInfo:
            def __init__(self):
                self.id = "test_id"
                self.status = "complete"
                self.result = "done"

        mock_job_instance.info.return_value = JobInfo()
        MockArqJob.return_value = mock_job_instance

        response = await client.get("/api/v1/tasks/task/test_id", headers=normal_user_token_headers)
        assert response.status_code == 200
        assert response.json()["id"] == "test_id"
        assert response.json()["status"] == "complete"
