import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeCodeStructureRecord,
    KnowledgeDiscoveredSeedRecord,
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationSearchRecord,
    KnowledgeInformationType,
    KnowledgeMatchedEntryPointsRecord,
    KnowledgeObject,
    KnowledgeObjectStructureRecord,
    KnowledgeRegistryEmbeddingKind,
    KnowledgeRegistryEmbeddingTarget,
    KnowledgeRegistryEmbeddingUpdate,
    KnowledgeSemanticSeedVectors,
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


logger = logging.getLogger(__name__)


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

    async def list_missing_registry_embeddings(
        self,
        *,
        document_type_ids: list[UUID],
        information_type_ids: list[UUID],
        information_field_ids: list[UUID],
        object_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[KnowledgeRegistryEmbeddingTarget]:

        targets: list[KnowledgeRegistryEmbeddingTarget] = []
        targets.extend(
            await self._missing_code_embeddings(
                model_class=KnowledgeDocumentTypeModel,
                ids=document_type_ids,
                kind=KnowledgeRegistryEmbeddingKind.DOCUMENT_TYPE,
            )
        )
        targets.extend(
            await self._missing_code_embeddings(
                model_class=KnowledgeInformationTypeModel,
                ids=information_type_ids,
                kind=KnowledgeRegistryEmbeddingKind.INFORMATION_TYPE,
            )
        )
        targets.extend(
            await self._missing_code_embeddings(
                model_class=KnowledgeInformationFieldModel,
                ids=information_field_ids,
                kind=KnowledgeRegistryEmbeddingKind.INFORMATION_FIELD,
            )
        )
        targets.extend(
            await self._missing_code_embeddings(
                model_class=KnowledgeTopicModel,
                ids=topic_ids,
                kind=KnowledgeRegistryEmbeddingKind.TOPIC,
            )
        )

        if object_ids:
            result = await self.session.execute(
                select(KnowledgeObjectModel).where(
                    KnowledgeObjectModel.id.in_(object_ids),
                    or_(
                        KnowledgeObjectModel.object_embedding.is_(None),
                        KnowledgeObjectModel.identifier_embedding.is_(None),
                    ),
                )
            )
            for model in result.scalars().all():
                if model.object_embedding is None:
                    targets.append(
                        KnowledgeRegistryEmbeddingTarget(
                            kind=KnowledgeRegistryEmbeddingKind.OBJECT,
                            id=model.id,
                            text=model.object_code,
                        )
                    )
                if (
                    model.identifier_code is not None
                    and model.identifier_embedding is None
                ):
                    targets.append(
                        KnowledgeRegistryEmbeddingTarget(
                            kind=KnowledgeRegistryEmbeddingKind.IDENTIFIER,
                            id=model.id,
                            text=model.identifier_code,
                        )
                    )
        return targets

    async def update_registry_embeddings(
        self,
        updates: list[KnowledgeRegistryEmbeddingUpdate],
    ) -> None:

        for update in updates:
            model_class, column_name = self._embedding_model_column(
                update.kind,
            )
            result = await self.session.execute(
                select(model_class).where(
                    model_class.id == update.id,
                )
            )
            model = result.scalar_one_or_none()
            if model is None:
                continue
            if getattr(model, column_name) is not None:
                continue
            setattr(model, column_name, update.embedding)
            if hasattr(model, "updated_at"):
                model.updated_at = datetime.now(timezone.utc)

        await self.session.flush()

    async def search_information(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        identifier_code: str | None,
        information_type_code: str | None,
        topic_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:

        logger.info(
            "[KNOWLEDGE_REPOSITORY] search start "
            "space=%s object=%s identifier=%s information_type=%s topics=%s",
            knowledge_space_id,
            object_code,
            identifier_code,
            information_type_code,
            topic_codes,
        )

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

        logger.info(
            "[KNOWLEDGE_REPOSITORY] object lookup "
            "object_code=%s identifier_code=%s found=%s",
            object_code,
            identifier_code,
            object_model is not None,
        )

        if object_model is None:
            logger.warning(
                "[KNOWLEDGE_REPOSITORY] object not found "
                "space=%s object_code=%s identifier_code=%s",
                knowledge_space_id,
                object_code,
                identifier_code,
            )
            return []

        logger.info(
            "[KNOWLEDGE_REPOSITORY] resolved object "
            "id=%s object_code=%s identifier_code=%s",
            object_model.id,
            object_model.object_code,
            object_model.identifier_code,
        )

        object_ref_filter = (
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
            )
        )

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
                object_ref_filter,
            )
        )

        # Diagnostic funnel for temporary retrieval debugging; remove after the
        # object/type/topic mismatch is identified.
        object_count = await self._count_information(
            knowledge_space_id=knowledge_space_id,
            object_ref_filter=object_ref_filter,
        )
        logger.info(
            "[KNOWLEDGE_REPOSITORY] after object filter count=%s",
            object_count,
        )

        if information_type_code is not None:
            statement = statement.where(
                KnowledgeInformationTypeModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationTypeModel.code
                == information_type_code,
            )

            information_type_count = await self._count_information(
                knowledge_space_id=knowledge_space_id,
                object_ref_filter=object_ref_filter,
                information_type_code=information_type_code,
            )
            logger.info(
                "[KNOWLEDGE_REPOSITORY] after information_type filter code=%s count=%s",
                information_type_code,
                information_type_count,
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

            topic_count = await self._count_information(
                knowledge_space_id=knowledge_space_id,
                object_ref_filter=object_ref_filter,
                information_type_code=information_type_code,
                topic_filters=topic_filters,
            )
            logger.info(
                "[KNOWLEDGE_REPOSITORY] after topic filter topics=%s count=%s",
                topic_codes,
                topic_count,
            )

        result = await self.session.execute(
            statement,
        )
        rows = result.all()

        logger.info(
            "[KNOWLEDGE_REPOSITORY] final result count=%s",
            len(rows),
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
            for model, information_type_code in rows
        ]

    async def discover(
        self,
        *,
        knowledge_space_id: UUID,
        seeds: list[dict[str, Any]],
        seed_vectors: list[KnowledgeSemanticSeedVectors] | None = None,
    ) -> list[KnowledgeDiscoveredSeedRecord]:

        discovered: list[KnowledgeDiscoveredSeedRecord] = []
        vectors_by_seed_id = {
            item.seed_id: item
            for item in seed_vectors or []
        }
        for seed in seeds:
            seed_record = await self._discover_seed(
                knowledge_space_id=knowledge_space_id,
                seed=seed,
                seed_vectors=vectors_by_seed_id.get(
                    str(seed["seed_id"]),
                ),
            )
            if seed_record is not None:
                discovered.append(seed_record)

        return discovered

    async def retrieve_for_selection(
        self,
        *,
        knowledge_space_id: UUID,
        discovered_seed: KnowledgeDiscoveredSeedRecord,
        information_type_codes: list[str],
        topic_codes: list[str],
        field_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:

        base_filters = self._entry_point_filters(
            knowledge_space_id=knowledge_space_id,
            discovered_seed=discovered_seed,
        )
        if not base_filters:
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
                or_(*base_filters),
            )
        )

        if information_type_codes:
            statement = statement.where(
                KnowledgeInformationTypeModel.code.in_(
                    information_type_codes,
                ),
            )

        topic_filters = self._topic_filters(topic_codes)
        if topic_filters:
            statement = statement.where(
                or_(*topic_filters),
            )

        field_filters = [
            KnowledgeInformationModel.data.has_key(field_code)
            for field_code in field_codes
        ]
        if field_filters:
            statement = statement.where(
                or_(*field_filters),
            )

        result = await self.session.execute(statement)
        rows = result.all()

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
            for model, information_type_code in rows
        ]

    async def _count_information(
        self,
        *,
        knowledge_space_id: UUID,
        object_ref_filter,
        information_type_code: str | None = None,
        topic_filters: list[Any] | None = None,
    ) -> int:

        statement = (
            select(
                func.count(KnowledgeInformationModel.id),
            )
            .select_from(KnowledgeInformationModel)
            .outerjoin(
                KnowledgeInformationTypeModel,
                KnowledgeInformationTypeModel.id
                == KnowledgeInformationModel.information_type_id,
            )
            .where(
                KnowledgeInformationModel.knowledge_space_id
                == knowledge_space_id,
                object_ref_filter,
            )
        )

        if information_type_code is not None:
            statement = statement.where(
                KnowledgeInformationTypeModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationTypeModel.code
                == information_type_code,
            )

        if topic_filters:
            statement = statement.where(
                or_(*topic_filters),
            )

        result = await self.session.execute(
            statement,
        )
        return int(result.scalar_one())

    async def _discover_seed(
        self,
        *,
        knowledge_space_id: UUID,
        seed: dict[str, Any],
        seed_vectors: KnowledgeSemanticSeedVectors | None = None,
    ) -> KnowledgeDiscoveredSeedRecord | None:

        matched_entry_points = KnowledgeMatchedEntryPointsRecord(
            objects=await self._match_objects(
                knowledge_space_id=knowledge_space_id,
                object_code=seed.get("object_code"),
                identifier_code=seed.get("identifier_code"),
                object_vector=(
                    seed_vectors.object_vector
                    if seed_vectors is not None
                    else None
                ),
                identifier_vector=(
                    seed_vectors.identifier_vector
                    if seed_vectors is not None
                    else None
                ),
            ),
            information_types=await self._match_information_types(
                knowledge_space_id=knowledge_space_id,
                information_type_code=seed.get(
                    "information_type_code",
                ),
                information_type_vector=(
                    seed_vectors.information_type_vector
                    if seed_vectors is not None
                    else None
                ),
            ),
            topics=await self._match_topics(
                knowledge_space_id=knowledge_space_id,
                topic_codes=seed.get("topic_codes", []),
                topic_vectors=(
                    seed_vectors.topic_vectors
                    if seed_vectors is not None
                    else None
                ),
            ),
        )
        base_filters = self._entry_point_filters_from_matches(
            knowledge_space_id=knowledge_space_id,
            matched_entry_points=matched_entry_points,
        )
        if not base_filters:
            return None

        rows = await self._load_reachable_structure_rows(
            knowledge_space_id=knowledge_space_id,
            base_filters=base_filters,
        )

        return KnowledgeDiscoveredSeedRecord(
            seed_id=str(seed["seed_id"]),
            matched_entry_points=matched_entry_points,
            available_objects=await self._available_objects(
                knowledge_space_id=knowledge_space_id,
                rows=rows,
            ),
            available_information_types=await (
                self._available_information_types(
                    knowledge_space_id=knowledge_space_id,
                    rows=rows,
                )
            ),
            available_topics=await self._available_topics(
                knowledge_space_id=knowledge_space_id,
                rows=rows,
            ),
            available_fields=await self._available_fields(
                knowledge_space_id=knowledge_space_id,
                rows=rows,
            ),
            constraints=dict(seed.get("constraints") or {}),
        )

    async def _match_objects(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str | None,
        identifier_code: str | None,
        object_vector: list[float] | None = None,
        identifier_vector: list[float] | None = None,
    ) -> list[KnowledgeObjectStructureRecord]:

        if object_code is None and identifier_code is None:
            return []

        exact_models = []
        if object_code is not None:
            statement = select(KnowledgeObjectModel).where(
                KnowledgeObjectModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeObjectModel.object_code == object_code,
            )
            if identifier_code is not None:
                statement = statement.where(
                    KnowledgeObjectModel.identifier_code
                    == identifier_code,
                )
            result = await self.session.execute(statement)
            exact_models = list(result.scalars().all())
        elif identifier_code is not None:
            result = await self.session.execute(
                select(KnowledgeObjectModel).where(
                    KnowledgeObjectModel.knowledge_space_id
                    == knowledge_space_id,
                    KnowledgeObjectModel.identifier_code
                    == identifier_code,
                )
            )
            exact_models = list(result.scalars().all())

        candidates = [
            self._object_record(model)
            for model in exact_models
        ]
        seen = {
            (
                item.object_code,
                item.identifier_code,
            )
            for item in candidates
        }

        if object_vector is not None:
            candidates.extend(
                await self._vector_object_candidates(
                    knowledge_space_id=knowledge_space_id,
                    vector=object_vector,
                    column=KnowledgeObjectModel.object_embedding,
                    seen=seen,
                )
            )
        if identifier_vector is not None:
            candidates.extend(
                await self._vector_object_candidates(
                    knowledge_space_id=knowledge_space_id,
                    vector=identifier_vector,
                    column=KnowledgeObjectModel.identifier_embedding,
                    seen=seen,
                )
            )
        return candidates

    async def _match_information_types(
        self,
        *,
        knowledge_space_id: UUID,
        information_type_code: str | None,
        information_type_vector: list[float] | None = None,
    ) -> list[KnowledgeCodeStructureRecord]:

        if information_type_code is None and information_type_vector is None:
            return []

        candidates = []
        if information_type_code is not None:
            result = await self.session.execute(
                select(KnowledgeInformationTypeModel).where(
                    KnowledgeInformationTypeModel.knowledge_space_id
                    == knowledge_space_id,
                    KnowledgeInformationTypeModel.code
                    == information_type_code,
                )
            )
            candidates.extend(
                self._information_type_record(model)
                for model in result.scalars().all()
            )

        candidates.extend(
            await self._vector_code_candidates(
                model_class=KnowledgeInformationTypeModel,
                record_factory=self._information_type_record,
                knowledge_space_id=knowledge_space_id,
                vector=information_type_vector,
                seen={item.code for item in candidates},
            )
        )
        return candidates

    async def _match_topics(
        self,
        *,
        knowledge_space_id: UUID,
        topic_codes: list[str],
        topic_vectors: dict[str, list[float]] | None = None,
    ) -> list[KnowledgeCodeStructureRecord]:

        if not topic_codes and not topic_vectors:
            return []

        candidates = []
        if topic_codes:
            result = await self.session.execute(
                select(KnowledgeTopicModel).where(
                    KnowledgeTopicModel.knowledge_space_id
                    == knowledge_space_id,
                    KnowledgeTopicModel.code.in_(topic_codes),
                )
            )
            candidates.extend(
                self._topic_record(model)
                for model in result.scalars().all()
            )

        seen = {item.code for item in candidates}
        for vector in (topic_vectors or {}).values():
            candidates.extend(
                await self._vector_code_candidates(
                    model_class=KnowledgeTopicModel,
                    record_factory=self._topic_record,
                    knowledge_space_id=knowledge_space_id,
                    vector=vector,
                    seen=seen,
                )
            )
        return candidates

    async def _load_reachable_structure_rows(
        self,
        *,
        knowledge_space_id: UUID,
        base_filters,
    ):

        result = await self.session.execute(
            select(
                KnowledgeInformationModel.information_type_id,
                KnowledgeInformationModel.object_refs,
                KnowledgeInformationModel.topic_refs,
                KnowledgeInformationModel.data,
            ).where(
                KnowledgeInformationModel.knowledge_space_id
                == knowledge_space_id,
                or_(*base_filters),
            )
        )
        return result.all()

    async def _available_objects(
        self,
        *,
        knowledge_space_id: UUID,
        rows,
    ) -> list[KnowledgeObjectStructureRecord]:

        object_ids = self._object_ids_from_rows(rows)
        if not object_ids:
            return []

        result = await self.session.execute(
            select(KnowledgeObjectModel).where(
                KnowledgeObjectModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeObjectModel.id.in_(object_ids),
            )
        )
        return [
            self._object_record(model)
            for model in result.scalars().all()
        ]

    async def _available_information_types(
        self,
        *,
        knowledge_space_id: UUID,
        rows,
    ) -> list[KnowledgeCodeStructureRecord]:

        type_ids = {
            row._mapping["information_type_id"]
            for row in rows
            if row._mapping["information_type_id"] is not None
        }
        if not type_ids:
            return []

        result = await self.session.execute(
            select(KnowledgeInformationTypeModel).where(
                KnowledgeInformationTypeModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationTypeModel.id.in_(type_ids),
            )
        )
        return [
            self._information_type_record(model)
            for model in result.scalars().all()
        ]

    async def _available_topics(
        self,
        *,
        knowledge_space_id: UUID,
        rows,
    ) -> list[KnowledgeCodeStructureRecord]:

        topic_codes = self._topic_codes_from_rows(rows)
        if not topic_codes:
            return []

        result = await self.session.execute(
            select(KnowledgeTopicModel).where(
                KnowledgeTopicModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeTopicModel.code.in_(topic_codes),
            )
        )
        return [
            self._topic_record(model)
            for model in result.scalars().all()
        ]

    async def _available_fields(
        self,
        *,
        knowledge_space_id: UUID,
        rows,
    ) -> list[KnowledgeCodeStructureRecord]:

        field_codes = self._field_codes_from_rows(rows)
        if not field_codes:
            return []

        result = await self.session.execute(
            select(KnowledgeInformationFieldModel).where(
                KnowledgeInformationFieldModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeInformationFieldModel.code.in_(field_codes),
            )
        )
        registry_fields = {
            model.code: self._field_record(model)
            for model in result.scalars().all()
        }
        return [
            registry_fields.get(
                code,
                KnowledgeCodeStructureRecord(
                    code=code,
                    name=None,
                    description=None,
                    data_type=None,
                ),
            )
            for code in sorted(field_codes)
        ]

    async def _vector_code_candidates(
        self,
        *,
        model_class,
        record_factory,
        knowledge_space_id: UUID,
        vector: list[float] | None,
        seen: set[str],
        top_k: int = 5,
    ) -> list[KnowledgeCodeStructureRecord]:

        if vector is None:
            return []

        distance = model_class.embedding.cosine_distance(vector)
        result = await self.session.execute(
            select(model_class)
            .where(
                model_class.knowledge_space_id == knowledge_space_id,
                model_class.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )

        records = []
        for model in result.scalars().all():
            if model.code in seen:
                continue
            seen.add(model.code)
            records.append(record_factory(model))
        return records

    async def _vector_object_candidates(
        self,
        *,
        knowledge_space_id: UUID,
        vector: list[float],
        column,
        seen: set[tuple[str, str | None]],
        top_k: int = 5,
    ) -> list[KnowledgeObjectStructureRecord]:

        distance = column.cosine_distance(vector)
        result = await self.session.execute(
            select(KnowledgeObjectModel)
            .where(
                KnowledgeObjectModel.knowledge_space_id
                == knowledge_space_id,
                column.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )

        records = []
        for model in result.scalars().all():
            key = (
                model.object_code,
                model.identifier_code,
            )
            if key in seen:
                continue
            seen.add(key)
            records.append(self._object_record(model))
        return records

    async def _missing_code_embeddings(
        self,
        *,
        model_class,
        ids: list[UUID],
        kind: KnowledgeRegistryEmbeddingKind,
    ) -> list[KnowledgeRegistryEmbeddingTarget]:

        if not ids:
            return []

        result = await self.session.execute(
            select(model_class).where(
                model_class.id.in_(ids),
                model_class.embedding.is_(None),
            )
        )
        return [
            KnowledgeRegistryEmbeddingTarget(
                kind=kind,
                id=model.id,
                text=model.code,
            )
            for model in result.scalars().all()
        ]

    @staticmethod
    def _embedding_model_column(
        kind: KnowledgeRegistryEmbeddingKind,
    ):

        mapping = {
            KnowledgeRegistryEmbeddingKind.DOCUMENT_TYPE: (
                KnowledgeDocumentTypeModel,
                "embedding",
            ),
            KnowledgeRegistryEmbeddingKind.TOPIC: (
                KnowledgeTopicModel,
                "embedding",
            ),
            KnowledgeRegistryEmbeddingKind.OBJECT: (
                KnowledgeObjectModel,
                "object_embedding",
            ),
            KnowledgeRegistryEmbeddingKind.IDENTIFIER: (
                KnowledgeObjectModel,
                "identifier_embedding",
            ),
            KnowledgeRegistryEmbeddingKind.INFORMATION_TYPE: (
                KnowledgeInformationTypeModel,
                "embedding",
            ),
            KnowledgeRegistryEmbeddingKind.INFORMATION_FIELD: (
                KnowledgeInformationFieldModel,
                "embedding",
            ),
        }
        return mapping[kind]

    def _entry_point_filters(
        self,
        *,
        knowledge_space_id: UUID,
        discovered_seed: KnowledgeDiscoveredSeedRecord,
    ):

        return self._entry_point_filters_from_matches(
            knowledge_space_id=knowledge_space_id,
            matched_entry_points=discovered_seed.matched_entry_points,
        )

    @staticmethod
    def _entry_point_filters_from_matches(
        *,
        knowledge_space_id: UUID,
        matched_entry_points: KnowledgeMatchedEntryPointsRecord,
    ):

        filters = []
        for object_ref in matched_entry_points.objects:
            filters.append(
                KnowledgeInformationModel.object_refs.contains(
                    [
                        {
                            "object_code": object_ref.object_code,
                            "identifier_code": (
                                object_ref.identifier_code
                            ),
                        },
                    ],
                )
            )
        filters.extend(
            KnowledgeInformationModel.information_type_id.in_(
                select(KnowledgeInformationTypeModel.id).where(
                    KnowledgeInformationTypeModel.knowledge_space_id
                    == knowledge_space_id,
                    KnowledgeInformationTypeModel.code
                    == information_type.code,
                )
            )
            for information_type in (
                matched_entry_points.information_types
            )
        )
        filters.extend(
            KnowledgeInformationModel.topic_refs.contains(
                [
                    {
                        "code": topic.code,
                    },
                ],
            )
            for topic in matched_entry_points.topics
        )
        return filters

    @staticmethod
    def _topic_filters(topic_codes: list[str]):

        return [
            KnowledgeInformationModel.topic_refs.contains(
                [
                    {
                        "code": topic_code,
                    },
                ],
            )
            for topic_code in topic_codes
        ]

    @staticmethod
    def _object_ids_from_rows(rows) -> set[UUID]:

        object_ids = set()
        for row in rows:
            for ref in row._mapping["object_refs"] or []:
                object_id = ref.get("object_id")
                if object_id:
                    object_ids.add(UUID(str(object_id)))
        return object_ids

    @staticmethod
    def _topic_codes_from_rows(rows) -> set[str]:

        topic_codes = set()
        for row in rows:
            for ref in row._mapping["topic_refs"] or []:
                code = ref.get("code")
                if code:
                    topic_codes.add(str(code))
        return topic_codes

    @staticmethod
    def _field_codes_from_rows(rows) -> set[str]:

        field_codes = set()
        for row in rows:
            data = row._mapping["data"]
            if isinstance(data, dict):
                field_codes.update(str(code) for code in data.keys())
        return field_codes

    @staticmethod
    def _object_record(
        model: KnowledgeObjectModel,
    ) -> KnowledgeObjectStructureRecord:

        return KnowledgeObjectStructureRecord(
            object_code=model.object_code,
            identifier_code=model.identifier_code,
            name=model.object_name,
            identifier_name=model.identifier_name,
            description=model.description,
        )

    @staticmethod
    def _information_type_record(
        model: KnowledgeInformationTypeModel,
    ) -> KnowledgeCodeStructureRecord:

        return KnowledgeCodeStructureRecord(
            code=model.code,
            name=model.name,
            description=model.description,
        )

    @staticmethod
    def _topic_record(
        model: KnowledgeTopicModel,
    ) -> KnowledgeCodeStructureRecord:

        return KnowledgeCodeStructureRecord(
            code=model.code,
            name=model.name,
            description=model.description,
        )

    @staticmethod
    def _field_record(
        model: KnowledgeInformationFieldModel,
    ) -> KnowledgeCodeStructureRecord:

        return KnowledgeCodeStructureRecord(
            code=model.code,
            name=model.name,
            description=model.description,
            data_type=model.data_type,
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
