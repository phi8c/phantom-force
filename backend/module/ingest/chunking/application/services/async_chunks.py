import asyncio


async def iterate_chunks(chunks):
    """Advance the synchronous reader off-loop with bounded, serial demand."""
    iterator = iter(chunks)
    end = object()
    try:
        while True:
            operation = asyncio.create_task(asyncio.to_thread(next, iterator, end))
            try:
                value = await asyncio.shield(operation)
            except asyncio.CancelledError:
                await asyncio.gather(operation, return_exceptions=True)
                raise
            if value is end:
                return
            yield value
    finally:
        close = getattr(iterator, 'close', None)
        if close is not None:
            await asyncio.to_thread(close)
