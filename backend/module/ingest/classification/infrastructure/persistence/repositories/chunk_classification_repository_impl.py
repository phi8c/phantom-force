from collections.abc import Iterable
from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.classification.domain.contracts.chunk_classification_repository import (
    ChunkClassificationRepository,
)
from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.infrastructure.persistence.mappers.chunk_classification_mapper import (
    ChunkClassificationMapper,
)
from module.ingest.classification.infrastructure.persistence.models.chunk_classification_model import (
    ChunkClassificationModel,
)
from module.ingest.chunking.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)


class ChunkClassificationRepositoryImpl(
    ChunkClassificationRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[ChunkClassification]:

        statement = select(
            ChunkClassificationModel
        ).join(
            DocumentChunkModel,
            DocumentChunkModel.id
            == ChunkClassificationModel.chunk_id,
        ).where(
            DocumentChunkModel.batch_id
            == batch_id,
        )

        result = await self.session.execute(
            statement,
        )

        return [
            ChunkClassificationMapper.to_entity(
                model
            )
            for model in result.scalars().all()
        ]

    async def upsert_many(
        self,
        classifications: Iterable[ChunkClassification],
    ) -> list[ChunkClassification]:

        now = datetime.now(
            timezone.utc,
        )

        rows = [
            {
                "id": (
                    classification.id
                    or uuid4()
                ),
                "chunk_id": classification.chunk_id,
                "model_name": classification.model_name,
                "label": classification.label,
                "confidence": classification.confidence,
                "raw_response": (
                    classification.raw_response
                ),
                "created_at": (
                    classification.created_at
                    or now
                ),
            }
            for classification in classifications
        ]

        if not rows:
            return []

        statement = insert(
            ChunkClassificationModel
        ).values(
            rows,
        )

        statement = statement.on_conflict_do_update(
            index_elements=[
                "chunk_id",
                "model_name",
            ],
            set_={
                "label": statement.excluded.label,
                "confidence": (
                    statement.excluded.confidence
                ),
                "raw_response": (
                    statement.excluded.raw_response
                ),
            },
        ).returning(
            ChunkClassificationModel
        )

        result = await self.session.execute(
            statement,
        )

        models = result.scalars().all()

        await self.session.flush()

        return [
            ChunkClassificationMapper.to_entity(
                model
            )
            for model in models
        ]
