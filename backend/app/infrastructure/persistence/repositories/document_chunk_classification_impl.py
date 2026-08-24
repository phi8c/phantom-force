from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_chunk_classification import (
    DocumentChunkClassification,
)
from app.domain.repositories.document_chunk_classification_repository import (
    DocumentChunkClassificationRepository,
)
from app.infrastructure.persistence.mappers.document_chunk_classification_mapper import (
    DocumentChunkClassificationMapper,
)
from app.infrastructure.persistence.models.document_chunk_classification_model import (
    DocumentChunkClassificationModel,
)


class DocumentChunkClassificationRepositoryImpl(
    DocumentChunkClassificationRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        classification: DocumentChunkClassification,
    ) -> DocumentChunkClassification:

        model = (
            DocumentChunkClassificationMapper.to_model(
                classification,
            )
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return (
            DocumentChunkClassificationMapper.to_domain(
                model,
            )
        )

    async def create_many(
        self,
        classifications: list[
            DocumentChunkClassification
        ],
    ) -> list[DocumentChunkClassification]:

        models = [
            DocumentChunkClassificationMapper.to_model(
                entity,
            )
            for entity in classifications
        ]

        self.session.add_all(
            models,
        )

        await self.session.flush()

        return [
            DocumentChunkClassificationMapper.to_domain(
                model,
            )
            for model in models
        ]

    async def list_by_chunk_id(
        self,
        chunk_id: UUID,
    ) -> list[DocumentChunkClassification]:

        result = await self.session.execute(
            select(
                DocumentChunkClassificationModel,
            ).where(
                DocumentChunkClassificationModel.chunk_id
                == chunk_id
            )
        )

        models = (
            result.scalars().all()
        )

        return [
            DocumentChunkClassificationMapper.to_domain(
                model,
            )
            for model in models
        ]