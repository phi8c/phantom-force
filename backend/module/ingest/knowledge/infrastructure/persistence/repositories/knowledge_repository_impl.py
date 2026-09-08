from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationSearchRecord,
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

    async def search_information(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        identifier_code: str | None,
        information_type_code: str | None,
        topic_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:

        object_statement = select(KnowledgeObjectModel).where(
            KnowledgeObjectModel.knowledge_space_id
            == knowledge_space_id,
            KnowledgeObjectModel.object_code == object_code,
        )
        if identifier_code is None:
            object_statement = object_statement.where(
                KnowledgeObjectModel.identifier_code.is_(None),
            )
        else:
            object_statement = object_statement.where(
                KnowledgeObjectModel.identifier_code
                == identifier_code,
            )

        object_result = await self.session.execute(
            object_statement,
        )
        object_model = object_result.scalar_one_or_none()
        if object_model is None:
            return []

        statement = (
            select(
                KnowledgeInformationModel,
                KnowledgeInformationTypeModel.code,
            )
            .outerjoin(
                KnowledgeInformationTypeModel,
                KnowledgeInformationTypeModel.id
                == KnowledgeInformationModel.information_type_id,
            )
            .where(
                KnowledgeInformationModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationModel.object_refs.contains(
                    [
                        {
                            "object_id": str(object_model.id),
                            "object_code": object_model.object_code,
                            "identifier_code": (
                                object_model.identifier_code
                            ),
                        },
                    ],
                ),
            )
        )

        if information_type_code is not None:
            statement = statement.where(
                KnowledgeInformationTypeModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationTypeModel.code
                == information_type_code,
            )

        topic_filters = [
            KnowledgeInformationModel.topic_refs.contains(
                [
                    {
                        "code": topic_code,
                    },
                ],
            )
            for topic_code in topic_codes
        ]
        if topic_filters:
            statement = statement.where(
                or_(*topic_filters),
            )

        result = await self.session.execute(
            statement,
        )

        return [
            KnowledgeInformationSearchRecord(
                information_id=model.id,
                information_type_code=information_type_code,
                summary=model.summary,
                data=model.data,
                object_refs=model.object_refs,
                topic_refs=model.topic_refs,
                source_refs=model.source_refs,
                confidence=model.confidence,
            )
            for model, information_type_code in result.all()
        ]

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
