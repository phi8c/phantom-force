from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeTopic,
)
from module.ingest.knowledge.infrastructure.persistence.mappers import (
    KnowledgeMapper,
)
from module.ingest.knowledge.infrastructure.persistence.models import (
    KnowledgeDocumentTypeModel,
    KnowledgeInformationFieldModel,
    KnowledgeInformationModel,
    KnowledgeInformationTypeModel,
    KnowledgeObjectModel,
    KnowledgeTopicModel,
)


class KnowledgeRepositoryImpl(KnowledgeRepository):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def upsert_document_type(
        self,
        entity: KnowledgeDocumentType,
    ) -> KnowledgeDocumentType:

        model = await self._get_by_space_code(
            KnowledgeDocumentTypeModel,
            entity.knowledge_space_id,
            entity.code,
        )

        if model is None:
            model = KnowledgeDocumentTypeModel(
                knowledge_space_id=entity.knowledge_space_id,
                code=entity.code,
                name=entity.name,
                description=entity.description,
                structuring_guidance=entity.structuring_guidance,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "name": entity.name,
                    "description": entity.description,
                    "structuring_guidance": entity.structuring_guidance,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.document_type_to_entity(
            model,
        )

    async def upsert_object(
        self,
        entity: KnowledgeObject,
    ) -> KnowledgeObject:

        statement = select(KnowledgeObjectModel).where(
            KnowledgeObjectModel.knowledge_space_id
            == entity.knowledge_space_id,
            KnowledgeObjectModel.object_code
            == entity.object_code,
        )

        if entity.identifier_code is None:
            statement = statement.where(
                KnowledgeObjectModel.identifier_code.is_(None),
            )
        else:
            statement = statement.where(
                KnowledgeObjectModel.identifier_code
                == entity.identifier_code,
            )

        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            model = KnowledgeObjectModel(
                knowledge_space_id=entity.knowledge_space_id,
                object_code=entity.object_code,
                identifier_code=entity.identifier_code,
                object_name=entity.object_name,
                identifier_name=entity.identifier_name,
                description=entity.description,
                aliases=entity.aliases,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "object_name": entity.object_name,
                    "identifier_name": entity.identifier_name,
                    "description": entity.description,
                    "aliases": entity.aliases,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.object_to_entity(
            model,
        )

    async def upsert_information_type(
        self,
        entity: KnowledgeInformationType,
    ) -> KnowledgeInformationType:

        model = await self._get_by_space_code(
            KnowledgeInformationTypeModel,
            entity.knowledge_space_id,
            entity.code,
        )
        if model is None:
            model = KnowledgeInformationTypeModel(
                knowledge_space_id=entity.knowledge_space_id,
                code=entity.code,
                name=entity.name,
                description=entity.description,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "name": entity.name,
                    "description": entity.description,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.information_type_to_entity(
            model,
        )

    async def upsert_information_field(
        self,
        entity: KnowledgeInformationField,
    ) -> KnowledgeInformationField:

        model = await self._get_by_space_code(
            KnowledgeInformationFieldModel,
            entity.knowledge_space_id,
            entity.code,
        )
        if model is None:
            model = KnowledgeInformationFieldModel(
                knowledge_space_id=entity.knowledge_space_id,
                code=entity.code,
                name=entity.name,
                description=entity.description,
                data_type=entity.data_type,
                unit_type=entity.unit_type,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "name": entity.name,
                    "description": entity.description,
                    "data_type": entity.data_type,
                    "unit_type": entity.unit_type,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.information_field_to_entity(
            model,
        )

    async def upsert_topic(
        self,
        entity: KnowledgeTopic,
    ) -> KnowledgeTopic:

        model = await self._get_by_space_code(
            KnowledgeTopicModel,
            entity.knowledge_space_id,
            entity.code,
        )
        if model is None:
            model = KnowledgeTopicModel(
                knowledge_space_id=entity.knowledge_space_id,
                code=entity.code,
                name=entity.name,
                description=entity.description,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "name": entity.name,
                    "description": entity.description,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.topic_to_entity(
            model,
        )

    async def upsert_information(
        self,
        entity: KnowledgeInformation,
        source_identity: dict[str, Any],
    ) -> KnowledgeInformation:

        result = await self.session.execute(
            select(
                KnowledgeInformationModel,
            ).where(
                KnowledgeInformationModel.knowledge_space_id
                == entity.knowledge_space_id,
                KnowledgeInformationModel.source_refs.contains(
                    [
                        source_identity,
                    ],
                ),
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            model = KnowledgeInformationModel(
                knowledge_space_id=entity.knowledge_space_id,
                information_type_id=entity.information_type_id,
                summary=entity.summary,
                data=entity.data,
                object_refs=entity.object_refs,
                topic_refs=entity.topic_refs,
                source_refs=entity.source_refs,
                confidence=entity.confidence,
                raw_model_output=entity.raw_model_output,
                metadata_payload=entity.metadata,
            )
            self.session.add(model)
        else:
            self._merge_non_null(
                model,
                {
                    "information_type_id": entity.information_type_id,
                    "summary": entity.summary,
                    "data": entity.data,
                    "object_refs": entity.object_refs,
                    "topic_refs": entity.topic_refs,
                    "source_refs": entity.source_refs,
                    "confidence": entity.confidence,
                    "raw_model_output": entity.raw_model_output,
                    "metadata_payload": entity.metadata,
                },
            )

        await self._flush_refresh(model)

        return KnowledgeMapper.information_to_entity(
            model,
        )

    async def _get_by_space_code(
        self,
        model_class,
        knowledge_space_id: UUID,
        code: str,
    ):

        result = await self.session.execute(
            select(model_class).where(
                model_class.knowledge_space_id
                == knowledge_space_id,
                model_class.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def _flush_refresh(
        self,
        model,
    ) -> None:

        if hasattr(model, "updated_at"):
            model.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(model)

    @staticmethod
    def _merge_non_null(
        model,
        values: dict[str, Any],
    ) -> None:

        for key, value in values.items():
            if value is not None:
                setattr(model, key, value)
