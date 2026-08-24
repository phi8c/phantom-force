from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_chunk import (
    DocumentChunk,
)
from app.domain.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.infrastructure.persistence.mappers.document_chunk_mapper import (
    DocumentChunkMapper,
)
from app.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)


class DocumentChunkRepositoryImpl(
    DocumentChunkRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        chunk: DocumentChunk,
    ) -> DocumentChunk:

        model = (
            DocumentChunkMapper.to_model(
                chunk,
            )
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return (
            DocumentChunkMapper.to_domain(
                model,
            )
        )

    async def create_many(
        self,
        chunks: list[
            DocumentChunk
        ],
    ) -> list[
        DocumentChunk
    ]:

        models = [
            DocumentChunkMapper.to_model(
                chunk,
            )
            for chunk in chunks
        ]

        self.session.add_all(
            models,
        )

        await self.session.flush()

        return [
            DocumentChunkMapper.to_domain(
                model,
            )
            for model in models
        ]

    async def get_by_id(
        self,
        chunk_id: UUID,
    ) -> DocumentChunk | None:

        result = await (
            self.session.execute(
                select(
                    DocumentChunkModel,
                ).where(
                    DocumentChunkModel.id
                    == chunk_id
                )
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            DocumentChunkMapper.to_domain(
                model,
            )
        )

    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[
        DocumentChunk
    ]:

        result = await (
            self.session.execute(
                select(
                    DocumentChunkModel,
                ).where(
                    DocumentChunkModel.batch_id
                    == batch_id
                ).order_by(
                    DocumentChunkModel.chunk_index,
                )
            )
        )

        models = (
            result.scalars().all()
        )

        return [
            DocumentChunkMapper.to_domain(
                model,
            )
            for model in models
        ]

    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[
        DocumentChunk
    ]:

        result = await (
            self.session.execute(
                select(
                    DocumentChunkModel,
                ).where(
                    DocumentChunkModel.document_id
                    == document_id
                ).order_by(
                    DocumentChunkModel.chunk_index,
                )
            )
        )

        models = (
            result.scalars().all()
        )

        return [
            DocumentChunkMapper.to_domain(
                model,
            )
            for model in models
        ]