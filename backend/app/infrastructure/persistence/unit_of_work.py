from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)


class SqlAlchemyUnitOfWork(
    UnitOfWork,
):
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def commit(
        self,
    ):
        await self.session.commit()

    async def rollback(
        self,
    ):
        await self.session.rollback()