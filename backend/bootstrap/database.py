from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

from anyio import CancelScope
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.database import SessionFactory


async_session_factory = SessionFactory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    context = async_session_factory()
    session = await context.__aenter__()
    try:
        yield session
    except BaseException as exc:
        await _close_session_context(
            context,
            type(exc),
            exc,
            exc.__traceback__,
        )
        raise
    else:
        await _close_session_context(
            context,
            None,
            None,
            None,
        )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session


async def _close_session_context(
    context,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    traceback: TracebackType | None,
) -> None:
    # Request cancellation must not interrupt rollback/close while a pooled
    # connection is still checked out.
    with CancelScope(shield=True):
        await context.__aexit__(
            exc_type,
            exc,
            traceback,
        )
