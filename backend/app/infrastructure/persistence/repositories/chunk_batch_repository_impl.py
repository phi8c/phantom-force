from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.domain.entities.chunk_batch import (
    ChunkBatch,
)
from app.domain.repositories.chunk_batch_repository import (
    ChunkBatchRepository,
)
from app.infrastructure.persistence.mappers.chunk_batch_mapper import (
    ChunkBatchMapper,
)
from app.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)


class ChunkBatchRepositoryImpl(
    ChunkBatchRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        batch: ChunkBatch,
    ) -> ChunkBatch:

        model = (
            ChunkBatchMapper.to_model(
                batch,
            )
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return (
            ChunkBatchMapper.to_domain(
                model,
            )
        )

    async def get_by_id(
        self,
        batch_id: UUID,
    ) -> ChunkBatch | None:

        result = await (
            self.session.execute(
                select(
                    ChunkBatchModel,
                ).where(
                    ChunkBatchModel.id
                    == batch_id
                )
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            ChunkBatchMapper.to_domain(
                model,
            )
        )

    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[ChunkBatch]:

        result = await (
            self.session.execute(
                select(
                    ChunkBatchModel,
                ).where(
                    ChunkBatchModel.document_id
                    == document_id
                ).order_by(
                    ChunkBatchModel.batch_index,
                )
            )
        )

        models = (
            result.scalars().all()
        )

        return [
            ChunkBatchMapper.to_domain(
                model,
            )
            for model in models
        ]
        
    async def mark_classification_completed(
    self,
    batch_id: UUID,
) -> None:

        await self.session.execute(
            update(
                ChunkBatchModel,
            )
            .where(
                ChunkBatchModel.id == batch_id,
            )
            .values(
                classification_completed=True,
            )
        )
        
    async def mark_embedding_completed(
    self,
    batch_id: UUID,
) -> None:

        await self.session.execute(
            update(
                ChunkBatchModel,
            )
            .where(
                ChunkBatchModel.id == batch_id,
            )
            .values(
                embedding_completed=True,
            )
        )
    
    async def try_complete_batch(
    self,
    batch_id: UUID,
) -> bool:

        result = await self.session.execute(
            update(
                ChunkBatchModel,
            )
            .where(
                ChunkBatchModel.id == batch_id,
                ChunkBatchModel.classification_completed.is_(
                    True,
                ),
                ChunkBatchModel.embedding_completed.is_(
                    True,
                ),
                ChunkBatchModel.batch_completed.is_(
                    False,
                ),
            )
            .values(
                batch_completed=True,
            )
        )

        return result.rowcount == 1
            
        