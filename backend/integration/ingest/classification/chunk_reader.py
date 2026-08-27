from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
    ChunkReader,
)


class ModuleChunkReader(
    ChunkReader,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[ChunkForClassification]:

        statement = (
            select(
                DocumentChunkModel
            )
            .where(
                DocumentChunkModel.batch_id
                == batch_id,
            )
            .order_by(
                DocumentChunkModel.chunk_index.asc(),
            )
        )

        result = await self.session.execute(
            statement,
        )

        return [
            ChunkForClassification(
                id=model.id,
                content=model.content,
                metadata=(
                    model.metadata_payload
                    or {}
                ),
            )
            for model in result.scalars().all()
        ]
