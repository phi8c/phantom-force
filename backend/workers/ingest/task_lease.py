"""Keep long-running execution fenced by an independently renewed lease."""
import asyncio
from collections.abc import Awaitable, Callable


async def execute_with_lease(
    operation: Awaitable,
    *,
    renew: Callable[[], Awaitable[bool]],
    completed: Callable[[], Awaitable[bool]],
    interval: float,
):
    execution = asyncio.ensure_future(operation)
    try:
        while not execution.done():
            done, _ = await asyncio.wait({execution}, timeout=interval)
            if done:
                break
            if not await renew() and not execution.done():
                if await completed():
                    return await execution
                raise RuntimeError('Task lease was lost')
        return await execution
    finally:
        if not execution.done():
            execution.cancel()
        await asyncio.gather(execution, return_exceptions=True)
