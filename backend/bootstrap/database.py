from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.database import SessionFactory


async_session_factory = SessionFactory


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:

    async with async_session_factory() as session:
        yield session
