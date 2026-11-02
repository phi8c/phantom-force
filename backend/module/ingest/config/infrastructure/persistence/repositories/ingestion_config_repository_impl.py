import base64
import json
from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
    IngestionJobPage,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)
from module.ingest.config.infrastructure.persistence.mappers.ingestion_job_configuration_mapper import (
    IngestionJobConfigurationMapper,
)
from module.ingest.config.infrastructure.persistence.mappers.ingestion_job_mapper import (
    IngestionJobMapper,
)
from module.ingest.config.infrastructure.persistence.models.ingestion_job_configuration_model import (
    IngestionJobConfigurationModel,
)
from module.ingest.config.infrastructure.persistence.models.ingestion_job_model import (
    IngestionJobModel,
)


class IngestionConfigRepositoryImpl(
    IngestionConfigRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_jobs(
        self,
        *,
        knowledge_space_id: UUID | None,
        status: str | None,
        limit: int,
        cursor: str | None,
    ) -> IngestionJobPage:
        created_at_cursor: datetime | None = None
        id_cursor: UUID | None = None

        if cursor:
            created_at_cursor, id_cursor = (
                self._decode_cursor(cursor)
            )

        statement = select(
            IngestionJobModel,
        )

        if knowledge_space_id is not None:
            statement = statement.where(
                IngestionJobModel.knowledge_space_id
                == knowledge_space_id,
            )

        if status:
            statement = statement.where(
                IngestionJobModel.status == status,
            )

        if created_at_cursor is not None and id_cursor is not None:
            statement = statement.where(
                or_(
                    IngestionJobModel.created_at
                    < created_at_cursor,
                    and_(
                        IngestionJobModel.created_at
                        == created_at_cursor,
                        IngestionJobModel.id < id_cursor,
                    ),
                )
            )

        statement = (
            statement.order_by(
                IngestionJobModel.created_at.desc(),
                IngestionJobModel.id.desc(),
            )
            .limit(limit + 1)
        )

        result = await self.session.execute(statement)
        models = list(result.scalars().all())
        has_more = len(models) > limit
        page_models = models[:limit]
        next_cursor = None

        if has_more and page_models:
            last_model = page_models[-1]
            next_cursor = self._encode_cursor(
                created_at=last_model.created_at,
                job_id=last_model.id,
            )

        return IngestionJobPage(
            items=[
                IngestionJobMapper.to_entity(model)
                for model in page_models
            ],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def get_job_by_id(
        self,
        job_id: UUID,
    ) -> IngestionJob | None:

        result = await self.session.execute(
            select(
                IngestionJobModel,
            ).where(
                IngestionJobModel.id == job_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return IngestionJobMapper.to_entity(
            model,
        )

    async def get_configuration_by_job_id(
        self,
        job_id: UUID,
    ) -> IngestionJobConfiguration | None:

        result = await self.session.execute(
            select(
                IngestionJobConfigurationModel,
            ).where(
                IngestionJobConfigurationModel.ingestion_job_id
                == job_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return (
            IngestionJobConfigurationMapper.to_entity(
                model,
            )
        )

    async def get_job_with_configuration(
        self,
        job_id: UUID,
    ) -> tuple[
        IngestionJob,
        IngestionJobConfiguration,
    ] | None:

        result = await self.session.execute(
            select(
                IngestionJobModel,
                IngestionJobConfigurationModel,
            )
            .join(
                IngestionJobConfigurationModel,
                IngestionJobConfigurationModel.ingestion_job_id
                == IngestionJobModel.id,
            )
            .where(
                IngestionJobModel.id == job_id,
            )
        )

        row = result.one_or_none()

        if row is None:
            return None

        job_model, configuration_model = row

        return (
            IngestionJobMapper.to_entity(
                job_model,
            ),
            IngestionJobConfigurationMapper.to_entity(
                configuration_model,
            ),
        )

    async def add_job(
        self,
        job: IngestionJob,
    ) -> IngestionJob:

        model = IngestionJobMapper.to_model(
            job,
        )

        self.session.add(
            model,
        )
        await self.session.flush()

        return IngestionJobMapper.to_entity(
            model,
        )

    async def add_configuration(
        self,
        configuration: IngestionJobConfiguration,
    ) -> IngestionJobConfiguration:

        model = IngestionJobConfigurationMapper.to_model(
            configuration,
        )

        self.session.add(
            model,
        )
        await self.session.flush()

        return (
            IngestionJobConfigurationMapper.to_entity(
                model,
            )
        )

    async def save_configuration(self, configuration: IngestionJobConfiguration) -> IngestionJobConfiguration:
        values = dict(is_classification=configuration.is_classification,
                      model_set_id=configuration.model_set_id,
                      chunking_strategy_id=configuration.chunking_strategy_id,
                      extraction_engine_id=configuration.extraction_engine_id,
                      configuration=configuration.configuration)
        statement = update(IngestionJobConfigurationModel).where(
            IngestionJobConfigurationModel.ingestion_job_id == configuration.ingestion_job_id,
        ).values(**values).returning(IngestionJobConfigurationModel)
        model = (await self.session.execute(statement)).scalar_one_or_none()
        if model is None:
            model = IngestionJobConfigurationMapper.to_model(configuration)
            self.session.add(model)
            await self.session.flush()
        return IngestionJobConfigurationMapper.to_entity(model)

    async def update_job_scope(self, *, job_id: UUID, scope_type: str | None,
                               scope_data: dict | None) -> IngestionJob:
        statement = update(IngestionJobModel).where(IngestionJobModel.id == job_id).values(
            scope_type=scope_type, scope_data=scope_data,
        ).returning(IngestionJobModel)
        model = (await self.session.execute(statement)).scalar_one_or_none()
        if model is None:
            raise LookupError('ingestion_job_id was not found')
        return IngestionJobMapper.to_entity(model)

    async def get_configuration_for_existing_job(self, job_id: UUID) -> IngestionJobConfiguration | None:
        statement = select(IngestionJobModel.id, IngestionJobConfigurationModel).outerjoin(
            IngestionJobConfigurationModel,
            IngestionJobConfigurationModel.ingestion_job_id == IngestionJobModel.id,
        ).where(IngestionJobModel.id == job_id)
        row = (await self.session.execute(statement)).one_or_none()
        if row is None:
            raise LookupError('ingestion_job_id was not found')
        return IngestionJobConfigurationMapper.to_entity(row[1]) if row[1] is not None else None

    async def mark_job_ready(
        self,
        *,
        job_id: UUID,
    ) -> IngestionJob:

        model = await self.session.get(
            IngestionJobModel,
            job_id,
        )

        if model is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        model.status = "READY"
        model.started_at = datetime.now(
            timezone.utc,
        )
        model.finished_at = None

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return IngestionJobMapper.to_entity(
            model,
        )

    @staticmethod
    def _encode_cursor(
        *,
        created_at: datetime,
        job_id: UUID,
    ) -> str:
        payload = json.dumps(
            {
                "created_at": created_at.isoformat(),
                "id": str(job_id),
            },
            separators=(",", ":"),
        ).encode("utf-8")

        return base64.urlsafe_b64encode(payload).decode("ascii")

    @staticmethod
    def _decode_cursor(
        cursor: str,
    ) -> tuple[datetime, UUID]:
        try:
            payload = json.loads(
                base64.urlsafe_b64decode(
                    cursor.encode("ascii"),
                ).decode("utf-8")
            )

            return (
                datetime.fromisoformat(
                    str(payload["created_at"]),
                ),
                UUID(str(payload["id"])),
            )
        except Exception as exc:
            raise ValueError(
                "Invalid ingestion jobs cursor"
            ) from exc
