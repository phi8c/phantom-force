from collections.abc import Iterable
from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.embedding.domain.contracts.document_chunk_embedding_repository import (
    DocumentChunkEmbeddingRepository,
)
from module.ingest.embedding.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)
from module.ingest.embedding.infrastructure.persistence.mappers.document_chunk_embedding_mapper import (
    DocumentChunkEmbeddingMapper,
)
from module.ingest.embedding.infrastructure.persistence.models.document_chunk_embedding_model import (
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

    async def get_by_chunk_and_model(
        self,
        chunk_id: UUID,
        model_name: str,
    ) -> DocumentChunkEmbedding | None:

        statement = select(
            DocumentChunkEmbeddingModel
        ).where(
            DocumentChunkEmbeddingModel.chunk_id
            == chunk_id,
            DocumentChunkEmbeddingModel.model_name
            == model_name,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return DocumentChunkEmbeddingMapper.to_entity(
            model,
        )

    async def upsert_many(
        self,
        embeddings: Iterable[DocumentChunkEmbedding],
    ) -> list[DocumentChunkEmbedding]:

        now = datetime.now(
            timezone.utc,
        )

        rows = [
            {
                "id": (
                    embedding.id
                    or uuid4()
                ),
                "chunk_id": embedding.chunk_id,
                "model_name": embedding.model_name,
                "embedding": embedding.embedding,
                "dimension": embedding.dimension,
                "token_count": embedding.token_count,
                "created_at": (
                    embedding.created_at
                    or now
                ),
            }
            for embedding in embeddings
        ]

        if not rows:
            return []

        statement = insert(
            DocumentChunkEmbeddingModel
        ).values(
            rows,
        )

        statement = statement.on_conflict_do_update(
            index_elements=[
                "chunk_id",
                "model_name",
            ],
            set_={
                "embedding": statement.excluded.embedding,
                "dimension": statement.excluded.dimension,
                "token_count": statement.excluded.token_count,
            },
        ).returning(
            DocumentChunkEmbeddingModel
        )

        result = await self.session.execute(
            statement,
        )

        models = result.scalars().all()

        await self.session.flush()

        return [
            DocumentChunkEmbeddingMapper.to_entity(
                model
            )
            for model in models
        ]
