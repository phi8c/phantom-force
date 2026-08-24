from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)
from app.domain.repositories.document_chunk_embedding_repository import (
    DocumentChunkEmbeddingRepository,
)
from app.infrastructure.persistence.mappers.document_chunk_embedding_mapper import (
    DocumentChunkEmbeddingMapper,
)
from app.infrastructure.persistence.models.document_chunk_embedding_model import (
    DocumentChunkEmbeddingModel,
)


class DocumentChunkEmbeddingRepositoryImpl(
    DocumentChunkEmbeddingRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        embedding: DocumentChunkEmbedding,
    ) -> DocumentChunkEmbedding:

        model = (
            DocumentChunkEmbeddingMapper.to_model(
                embedding,
            )
        )

        self.session.add(model)

        await self.session.flush()

        return (
            DocumentChunkEmbeddingMapper.to_domain(
                model,
            )
        )

    async def create_many(
        self,
        embeddings: list[
            DocumentChunkEmbedding
        ],
    ) -> list[DocumentChunkEmbedding]:

        models = [
            DocumentChunkEmbeddingMapper.to_model(
                entity,
            )
            for entity in embeddings
        ]

        self.session.add_all(models)

        await self.session.flush()

        return [
            DocumentChunkEmbeddingMapper.to_domain(
                model,
            )
            for model in models
        ]

    async def update(
        self,
        embedding: DocumentChunkEmbedding,
    ) -> DocumentChunkEmbedding:

        model = await self.session.get(
            DocumentChunkEmbeddingModel,
            embedding.id,
        )

        model.embedding = embedding.embedding
        model.dimension = embedding.dimension
        model.token_count = embedding.token_count

        await self.session.flush()

        return (
            DocumentChunkEmbeddingMapper.to_domain(
                model,
            )
        )

    async def get_by_chunk_and_model(
        self,
        chunk_id: UUID,
        model_name: str,
    ) -> DocumentChunkEmbedding | None:

        result = await self.session.execute(
            select(
                DocumentChunkEmbeddingModel,
            ).where(
                DocumentChunkEmbeddingModel.chunk_id == chunk_id,
                DocumentChunkEmbeddingModel.model_name == model_name,
            )
        )

        model = result.scalar_one_or_none()

        if not model:
            return None

        return (
            DocumentChunkEmbeddingMapper.to_domain(
                model,
            )
        )

    async def list_by_chunk_id(
        self,
        chunk_id: UUID,
    ) -> list[DocumentChunkEmbedding]:

        result = await self.session.execute(
            select(
                DocumentChunkEmbeddingModel,
            ).where(
                DocumentChunkEmbeddingModel.chunk_id == chunk_id,
            )
        )

        models = result.scalars().all()

        return [
            DocumentChunkEmbeddingMapper.to_domain(
                model,
            )
            for model in models
        ]