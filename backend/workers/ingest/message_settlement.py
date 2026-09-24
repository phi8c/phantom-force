from __future__ import annotations

import asyncio
import logging

from shared.messaging.contracts import ReceivedMessage


async def nack_with_backoff(
    message: ReceivedMessage,
    *,
    logger: logging.Logger,
    worker_name: str,
    delay_seconds: float = 5,
) -> None:
    try:
        await message.nack(requeue=True)
    except Exception:
        logger.exception("%s nack_failed", worker_name)
    await asyncio.sleep(delay_seconds)
