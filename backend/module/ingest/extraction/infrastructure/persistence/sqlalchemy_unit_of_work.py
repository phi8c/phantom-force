from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.extraction.domain.contracts.unit_of_work import (
    UnitOfWork,
)


class SQLAlchemyUnitOfWork(
    UnitOfWork,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def commit(
        self,
    ) -> None:

        await self.session.commit()

    async def rollback(
        self,
    ) -> None:

        await self.session.rollback()
