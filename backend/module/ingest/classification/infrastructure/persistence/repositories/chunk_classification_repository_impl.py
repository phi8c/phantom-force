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
        ).where(
            ChunkClassificationModel.batch_id
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
                "batch_id": classification.batch_id,
                "chunk_id": classification.chunk_id,
                "sensitivity": classification.sensitivity,
                "metadata_payload": (
                    classification.metadata
                    or {}
                ),
                "created_at": (
                    classification.created_at
                    or now
                ),
                "updated_at": (
                    classification.updated_at
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
                "batch_id",
                "chunk_id",
            ],
            set_={
                "sensitivity": statement.excluded.sensitivity,
                "metadata_payload": (
                    statement.excluded.metadata_payload
                ),
                "updated_at": statement.excluded.updated_at,
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
