import asyncio

from arq.worker import Worker


async def sample_background_task(ctx: Worker, name: str) -> str:
    """
    A sample background task that just sleeps for 5 seconds.
    """
    await asyncio.sleep(5)
    return f"Task {name} is complete!"
