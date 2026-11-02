import logging
import hashlib
from copy import deepcopy
from datetime import datetime
from datetime import timezone
from time import perf_counter
from typing import Any
from uuid import UUID
from shared.logging.chat_diagnostics import print_chat_trace

from sqlalchemy import func, case
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeCodeStructureRecord,
    KnowledgeDiscoveredRequestRecord,
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationSearchRecord,
    KnowledgeInformationType,
    KnowledgeMatchedEntryPointsRecord,
    KnowledgeObject,
    KnowledgeObjectResolutionCandidate,
    KnowledgeObjectStructureRecord,
    KnowledgeRegistryEmbeddingKind,
    KnowledgeRegistryEmbeddingTarget,
    KnowledgeRegistryEmbeddingUpdate,
    KnowledgeSemanticRequestVectors,
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
from module.ingest.knowledge.domain.object_semantics import (
    EMBEDDING_TEXT_VERSION,
    identifier_embedding_text,
    object_embedding_text,
)


from module.ingest.knowledge.infrastructure.persistence.queries.discovery_cache import vector_candidate_scope, vector_candidates
from module.ingest.knowledge.infrastructure.persistence.queries.retrieval_projection import (
    ReachableStructureQuery, structure_options, information_options,
)


logger = logging.getLogger(__name__)


class KnowledgeRepositoryImpl(KnowledgeRepository):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def acquire_object_resolution_lock(
        self, *, knowledge_space_id: UUID, object_code: str
    ) -> None:
        lock_source = f"{knowledge_space_id}:{object_code}".encode("utf-8")
        lock_key = int.from_bytes(
            hashlib.sha256(lock_source).digest()[:8],
            "big",
            signed=True,
        )
        await self.session.execute(select(func.pg_advisory_xact_lock(lock_key)))

    async def find_object_exact(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        identifier_code: str | None,
    ) -> KnowledgeObject | None:
        statement = select(KnowledgeObjectModel).where(
            KnowledgeObjectModel.knowledge_space_id == knowledge_space_id,
            KnowledgeObjectModel.object_code == object_code,
        )
        statement = statement.where(
            KnowledgeObjectModel.identifier_code.is_(None)
            if identifier_code is None
            else KnowledgeObjectModel.identifier_code == identifier_code
        )
        model = (await self.session.execute(statement)).scalar_one_or_none()
        return KnowledgeMapper.object_to_entity(model) if model is not None else None

    async def list_objects_by_type(
        self, *, knowledge_space_id: UUID, object_code: str
    ) -> list[KnowledgeObject]:
        result = await self.session.execute(
            select(KnowledgeObjectModel).where(
                KnowledgeObjectModel.knowledge_space_id == knowledge_space_id,
                KnowledgeObjectModel.object_code == object_code,
            )
        )
        return [
            KnowledgeMapper.object_to_entity(model)
            for model in result.scalars().all()
        ]

    async def find_similar_objects(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        object_embedding: list[float],
        identifier_embedding: list[float] | None,
        limit: int,
    ) -> list[KnowledgeObjectResolutionCandidate]:
        object_distance = KnowledgeObjectModel.object_embedding.cosine_distance(
            object_embedding,
        )
        if identifier_embedding is None:
            distance = object_distance
        else:
            identifier_distance = (
                KnowledgeObjectModel.identifier_embedding.cosine_distance(
                    identifier_embedding,
                )
            )
            distance = func.least(object_distance, identifier_distance)
        statement = (
            select(KnowledgeObjectModel, distance.label("distance"))
            .where(
                KnowledgeObjectModel.knowledge_space_id == knowledge_space_id,
                KnowledgeObjectModel.object_code == object_code,
                KnowledgeObjectModel.object_embedding.is_not(None),
            )
            .order_by(distance)
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        return [
            KnowledgeObjectResolutionCandidate(
                object=KnowledgeMapper.object_to_entity(model),
                distance=float(candidate_distance),
            )
            for model, candidate_distance in rows
            if candidate_distance is not None
        ]

    async def add_verified_object_aliases(
        self, *, object_id: UUID, aliases: list[str]
    ) -> KnowledgeObject:
        result = await self.session.execute(
            select(KnowledgeObjectModel)
            .where(KnowledgeObjectModel.id == object_id)
            .with_for_update()
        )
        model = result.scalar_one()
        if isinstance(model.aliases, dict):
            payload = deepcopy(model.aliases)
            existing = list(payload.get("verified", []))
        else:
            payload = None
            existing = list(model.aliases) if isinstance(model.aliases, list) else []
        normalized = {
            str(value).strip().casefold()
            for value in existing
            if isinstance(value, str)
        }
        for alias in aliases:
            if alias.strip().casefold() not in normalized:
                existing.append(alias)
                normalized.add(alias.strip().casefold())
        if payload is None:
            model.aliases = existing
        else:
            payload["verified"] = existing
            model.aliases = payload
        model.updated_at = datetime.now(timezone.utc)
        await self._flush_refresh(model)
        return KnowledgeMapper.object_to_entity(model)

    async def upsert_document_type(
        self,
        entity: KnowledgeDocumentType,
    ) -> KnowledgeDocumentType:

        model = await self._upsert_by_space_code(
            model_class=KnowledgeDocumentTypeModel,
            values={
                "knowledge_space_id": entity.knowledge_space_id,
                "code": entity.code,
                "name": entity.name,
                "description": entity.description,
                "structuring_guidance": entity.structuring_guidance,
                "metadata_payload": entity.metadata,
            },
            merge_columns=[
                "name",
                "description",
                "structuring_guidance",
                "metadata_payload",
            ],
        )
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
                    "metadata_payload": entity.metadata,
                },
            )
            model.aliases = self._merge_aliases(
                model.aliases,
                entity.aliases,
            )

        await self._flush_refresh(model)
        return KnowledgeMapper.object_to_entity(
            model,
        )

    async def upsert_information_type(
        self,
        entity: KnowledgeInformationType,
    ) -> KnowledgeInformationType:

        model = await self._upsert_by_space_code(
            model_class=KnowledgeInformationTypeModel,
            values={
                "knowledge_space_id": entity.knowledge_space_id,
                "code": entity.code,
                "name": entity.name,
                "description": entity.description,
                "metadata_payload": entity.metadata,
            },
            merge_columns=[
                "name",
                "description",
                "metadata_payload",
            ],
        )
        return KnowledgeMapper.information_type_to_entity(
            model,
        )

    async def upsert_information_types(
        self,
        entities: list[KnowledgeInformationType],
    ) -> list[KnowledgeInformationType]:
        if not entities:
            return []
        models = await self._upsert_many_by_space_code(
            model_class=KnowledgeInformationTypeModel,
            values=[
                {
                    "knowledge_space_id": entity.knowledge_space_id,
                    "code": entity.code,
                    "name": entity.name,
                    "description": entity.description,
                    "metadata_payload": entity.metadata,
                }
                for entity in entities
            ],
            merge_columns=[
                "name",
                "description",
                "metadata_payload",
            ],
        )
        return [
            KnowledgeMapper.information_type_to_entity(model)
            for model in models
        ]

    async def upsert_information_field(
        self,
        entity: KnowledgeInformationField,
    ) -> KnowledgeInformationField:

        model = await self._upsert_by_space_code(
            model_class=KnowledgeInformationFieldModel,
            values={
                "knowledge_space_id": entity.knowledge_space_id,
                "code": entity.code,
                "name": entity.name,
                "description": entity.description,
                "data_type": entity.data_type,
                "unit_type": entity.unit_type,
                "metadata_payload": entity.metadata,
            },
            merge_columns=[
                "name",
                "description",
                "data_type",
                "unit_type",
                "metadata_payload",
            ],
        )
        return KnowledgeMapper.information_field_to_entity(
            model,
        )

    async def upsert_information_fields(
        self,
        entities: list[KnowledgeInformationField],
    ) -> list[KnowledgeInformationField]:
        if not entities:
            return []
        models = await self._upsert_many_by_space_code(
            model_class=KnowledgeInformationFieldModel,
            values=[
                {
                    "knowledge_space_id": entity.knowledge_space_id,
                    "code": entity.code,
                    "name": entity.name,
                    "description": entity.description,
                    "data_type": entity.data_type,
                    "unit_type": entity.unit_type,
                    "metadata_payload": entity.metadata,
                }
                for entity in entities
            ],
            merge_columns=[
                "name",
                "description",
                "data_type",
                "unit_type",
                "metadata_payload",
            ],
        )
        return [
            KnowledgeMapper.information_field_to_entity(model)
            for model in models
        ]

    async def upsert_topic(
        self,
        entity: KnowledgeTopic,
    ) -> KnowledgeTopic:

        model = await self._upsert_by_space_code(
            model_class=KnowledgeTopicModel,
            values={
                "knowledge_space_id": entity.knowledge_space_id,
                "code": entity.code,
                "name": entity.name,
                "description": entity.description,
                "metadata_payload": entity.metadata,
            },
            merge_columns=[
                "name",
                "description",
                "metadata_payload",
            ],
        )
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
                )
            )
            for model in result.scalars().all():
                entity = KnowledgeMapper.object_to_entity(model)
                versions = (model.metadata_payload or {}).get(
                    "embedding_text_versions",
                    {},
                )
                if (
                    model.object_embedding is None
                    or versions.get("object") != EMBEDDING_TEXT_VERSION
                ):
                    targets.append(
                        KnowledgeRegistryEmbeddingTarget(
                            kind=KnowledgeRegistryEmbeddingKind.OBJECT,
                            id=model.id,
                            text=object_embedding_text(entity),
                            text_version=EMBEDDING_TEXT_VERSION,
                        )
                    )
                if (
                    model.identifier_code is not None
                    and (
                        model.identifier_embedding is None
                        or versions.get("identifier") != EMBEDDING_TEXT_VERSION
                    )
                ):
                    text = identifier_embedding_text(entity)
                    if text is None:
                        continue
                    targets.append(
                        KnowledgeRegistryEmbeddingTarget(
                            kind=KnowledgeRegistryEmbeddingKind.IDENTIFIER,
                            id=model.id,
                            text=text,
                            text_version=EMBEDDING_TEXT_VERSION,
                        )
                    )
        return targets

    async def update_registry_embeddings(
        self,
        updates: list[KnowledgeRegistryEmbeddingUpdate],
    ) -> None:

        grouped_updates: dict[
            tuple[type, str],
            list[KnowledgeRegistryEmbeddingUpdate],
        ] = {}
        for update in updates:
            key = self._embedding_model_column(update.kind)
            grouped_updates.setdefault(key, []).append(update)

        for (model_class, column_name), model_updates in grouped_updates.items():
            result = await self.session.execute(
                select(model_class).where(
                    model_class.id.in_(
                        [update.id for update in model_updates],
                    ),
                )
            )
            models_by_id = {
                model.id: model
                for model in result.scalars().all()
            }
            for update in model_updates:
                model = models_by_id.get(update.id)
                if model is None:
                    continue
                if (
                    getattr(model, column_name) is not None
                    and update.text_version is None
                ):
                    continue
                setattr(model, column_name, update.embedding)
                if (
                    update.text_version is not None
                    and isinstance(model, KnowledgeObjectModel)
                ):
                    metadata = dict(model.metadata_payload or {})
                    versions = dict(
                        metadata.get("embedding_text_versions", {})
                    )
                    versions[update.kind.value] = update.text_version
                    metadata["embedding_text_versions"] = versions
                    model.metadata_payload = metadata
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

        object_statement = select(KnowledgeObjectModel).options(structure_options(KnowledgeObjectModel)).where(
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
            .options(information_options())
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
        requests: list[dict[str, Any]],
        request_vectors: list[KnowledgeSemanticRequestVectors] | None = None,
    ) -> list[KnowledgeDiscoveredRequestRecord]:

        started_at = perf_counter()
        logger.info(
            "[KNOWLEDGE_REPOSITORY] discover_start space=%s request_count=%s has_vectors=%s",
            knowledge_space_id,
            len(requests),
            bool(request_vectors),
        )
        discovered: list[KnowledgeDiscoveredRequestRecord] = []
        vectors_by_request_id = {
            item.request_id: item
            for item in request_vectors or []
        }
        with vector_candidate_scope():
            for request in requests:
                request_record = await self._discover_request(
                    knowledge_space_id=knowledge_space_id,
                    request=request,
                    request_vectors=vectors_by_request_id.get(
                        str(request["request_id"]),
                    ),
                )
                if request_record is not None:
                    discovered.append(request_record)

        logger.info(
            "[KNOWLEDGE_REPOSITORY] discover_done space=%s elapsed_ms=%s discovered_count=%s",
            knowledge_space_id,
            int((perf_counter() - started_at) * 1000),
            len(discovered),
        )
        return discovered

    async def retrieve_for_selection(
        self,
        *,
        knowledge_space_id: UUID,
        discovered_request: KnowledgeDiscoveredRequestRecord,
        information_type_codes: list[str],
        topic_codes: list[str],
        field_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:

        base_filters = self._entry_point_filters(
            knowledge_space_id=knowledge_space_id,
            discovered_request=discovered_request,
        )
        if not base_filters:
            return []

        statement = (
            select(
                KnowledgeInformationModel,
                KnowledgeInformationTypeModel.code,
            )
            .options(information_options())
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

    async def _discover_request(
        self,
        *,
        knowledge_space_id: UUID,
        request: dict[str, Any],
        request_vectors: KnowledgeSemanticRequestVectors | None = None,
    ) -> KnowledgeDiscoveredRequestRecord | None:

        started_at = perf_counter()
        request_id = str(request["request_id"])
        logger.info(
            "[KNOWLEDGE_REPOSITORY] discover_request_start request_id=%s object_seeds=%s identifier_seeds=%s information_type_seeds=%s topic_seeds=%s field_seeds=%s has_vectors=%s",
            request_id,
            request.get("object_seeds") or [],
            request.get("identifier_seeds") or [],
            request.get("information_type_seeds") or [],
            request.get("topic_seeds") or [],
            request.get("information_field_seeds") or [],
            request_vectors is not None,
        )
        matched_entry_points = KnowledgeMatchedEntryPointsRecord(
            objects=await self._match_objects_from_seeds(
                knowledge_space_id=knowledge_space_id,
                object_codes=self._seed_values(
                    request,
                    "object_seeds",
                ),
                identifier_codes=self._seed_values(
                    request,
                    "identifier_seeds",
                ),
                object_vectors=(
                    request_vectors.object_vectors
                    if request_vectors is not None
                    else None
                ),
                identifier_vectors=(
                    request_vectors.identifier_vectors
                    if request_vectors is not None
                    else None
                ),
            ),
            information_types=await self._match_code_registry(
                model_class=KnowledgeInformationTypeModel,
                record_factory=self._information_type_record,
                knowledge_space_id=knowledge_space_id,
                codes=self._seed_values(
                    request,
                    "information_type_seeds",
                ),
                vectors=(
                    request_vectors.information_type_vectors
                    if request_vectors is not None
                    else None
                ),
            ),
            topics=await self._match_code_registry(
                model_class=KnowledgeTopicModel,
                record_factory=self._topic_record,
                knowledge_space_id=knowledge_space_id,
                codes=self._seed_values(
                    request,
                    "topic_seeds",
                ),
                vectors=(
                    request_vectors.topic_vectors
                    if request_vectors is not None
                    else None
                ),
            ),
            fields=await self._match_code_registry(
                model_class=KnowledgeInformationFieldModel,
                record_factory=self._field_record,
                knowledge_space_id=knowledge_space_id,
                codes=self._seed_values(
                    request,
                    "information_field_seeds",
                ),
                vectors=(
                    request_vectors.information_field_vectors
                    if request_vectors is not None
                    else None
                ),
            ),
        )
        base_filters = self._entry_point_filters_from_matches(
            knowledge_space_id=knowledge_space_id,
            matched_entry_points=matched_entry_points,
        )
        if not base_filters:
            logger.info(
                "[KNOWLEDGE_REPOSITORY] discover_request_no_entry_points request_id=%s elapsed_ms=%s",
                request_id,
                int((perf_counter() - started_at) * 1000),
            )
            return None

        topic_filters = self._topic_filters(
            [topic.code for topic in matched_entry_points.topics]
        )
        step_started_at = perf_counter()
        rows = await self._load_reachable_structure_rows(
            knowledge_space_id=knowledge_space_id,
            base_filters=topic_filters or base_filters,
        )
        logger.info(
            "[KNOWLEDGE_REPOSITORY] discover_request_reachable_loaded request_id=%s elapsed_ms=%s row_count=%s",
            request_id,
            int((perf_counter() - step_started_at) * 1000),
            len(rows),
        )

        available = await self._available_structure(knowledge_space_id=knowledge_space_id, rows=rows)
        record = KnowledgeDiscoveredRequestRecord(
            request_id=request_id,
            matched_entry_points=matched_entry_points,
            need=str(request.get("need") or ""),
            original_seeds={
                "document_type_seeds": list(
                    request.get("document_type_seeds") or [],
                ),
                "head_seeds": list(request.get("head_seeds") or []),
                "topic_seeds": list(request.get("topic_seeds") or []),
                "object_seeds": list(request.get("object_seeds") or []),
                "identifier_seeds": list(
                    request.get("identifier_seeds") or [],
                ),
                "information_type_seeds": list(
                    request.get("information_type_seeds") or [],
                ),
                "information_field_seeds": list(
                    request.get("information_field_seeds") or [],
                ),
            },
            available_objects=available.objects,
            available_information_types=available.information_types,
            available_topics=available.topics,
            available_fields=available.fields,
            constraints=dict(request.get("constraints") or {}),
        )
        logger.info(
            "[KNOWLEDGE_REPOSITORY] discover_request_done request_id=%s elapsed_ms=%s matched_objects=%s matched_information_types=%s matched_topics=%s matched_fields=%s available_objects=%s available_information_types=%s available_topics=%s available_fields=%s",
            request_id,
            int((perf_counter() - started_at) * 1000),
            len(record.matched_entry_points.objects),
            len(record.matched_entry_points.information_types),
            len(record.matched_entry_points.topics),
            len(record.matched_entry_points.fields),
            len(record.available_objects),
            len(record.available_information_types),
            len(record.available_topics),
            len(record.available_fields),
        )
        return record

    async def _match_objects_from_seeds(
        self,
        *,
        knowledge_space_id: UUID,
        object_codes: list[str],
        identifier_codes: list[str],
        object_vectors: dict[str, list[float]] | None = None,
        identifier_vectors: dict[str, list[float]] | None = None,
    ) -> list[KnowledgeObjectStructureRecord]:

        if (
            not object_codes
            and not identifier_codes
            and not object_vectors
            and not identifier_vectors
        ):
            return []

        candidates: list[KnowledgeObjectStructureRecord] = []
        seen: set[tuple[str, str | None]] = set()

        exact_filters = []
        if object_codes:
            exact_filters.append(
                KnowledgeObjectModel.object_code.in_(object_codes)
            )
        if identifier_codes:
            exact_filters.append(
                KnowledgeObjectModel.identifier_code.in_(identifier_codes)
            )
        if exact_filters:
            result = await self.session.execute(
                select(KnowledgeObjectModel).options(structure_options(KnowledgeObjectModel)).where(
                    KnowledgeObjectModel.knowledge_space_id
                    == knowledge_space_id,
                    or_(*exact_filters),
                )
            )
            for model in result.scalars().all():
                self._append_object_candidate(
                    candidates,
                    seen,
                    self._object_record(model),
                )

        print_chat_trace("OBJECT_EXACT_MATCHES", {
            "object_seeds": object_codes,
            "identifier_seeds": identifier_codes,
            "matches": candidates,
        })

        for seed, vector in (object_vectors or {}).items():
            matches = await self._vector_object_candidates(
                knowledge_space_id=knowledge_space_id,
                vector=vector,
                column=KnowledgeObjectModel.object_embedding,
                seen=seen,
            )
            print_chat_trace("OBJECT_VECTOR_MATCHES", {
                "seed": seed,
                "matches": matches,
            })
            candidates.extend(matches)

        for seed, vector in (identifier_vectors or {}).items():
            matches = await self._vector_object_candidates(
                knowledge_space_id=knowledge_space_id,
                vector=vector,
                column=KnowledgeObjectModel.identifier_embedding,
                seen=seen,
            )
            print_chat_trace("IDENTIFIER_VECTOR_MATCHES", {
                "seed": seed,
                "matches": matches,
            })
            candidates.extend(matches)

        logger.info(
            "[KNOWLEDGE_REPOSITORY] match_objects_from_seeds space=%s object_seed_count=%s identifier_seed_count=%s candidate_count=%s",
            knowledge_space_id,
            len(object_codes),
            len(identifier_codes),
            len(candidates),
        )
        return candidates

    async def _match_code_registry(
        self,
        *,
        model_class,
        record_factory,
        knowledge_space_id: UUID,
        codes: list[str],
        vectors: dict[str, list[float]] | None = None,
    ) -> list[KnowledgeCodeStructureRecord]:

        if not codes and not vectors:
            return []

        candidates: list[KnowledgeCodeStructureRecord] = []
        seen: set[str] = set()

        if codes:
            result = await self.session.execute(
                select(model_class).options(structure_options(model_class)).where(
                    model_class.knowledge_space_id
                    == knowledge_space_id,
                    model_class.code.in_(codes),
                )
            )
            models_by_code = {
                model.code: model
                for model in result.scalars().all()
            }
            for code in codes:
                model = models_by_code.get(code)
                if model is None or code in seen:
                    continue
                seen.add(code)
                candidates.append(record_factory(model))

        print_chat_trace("REGISTRY_EXACT_MATCHES", {
            "registry": model_class.__tablename__,
            "seeds": codes,
            "matches": candidates,
        })

        for seed, vector in (vectors or {}).items():
            matches = await self._vector_code_candidates(
                model_class=model_class,
                record_factory=record_factory,
                knowledge_space_id=knowledge_space_id,
                vector=vector,
                seen=seen,
            )
            print_chat_trace("REGISTRY_VECTOR_MATCHES", {
                "registry": model_class.__tablename__,
                "seed": seed,
                "matches": matches,
            })
            candidates.extend(matches)

        logger.info(
            "[KNOWLEDGE_REPOSITORY] match_code_registry table=%s space=%s seed_count=%s candidate_count=%s",
            model_class.__tablename__,
            knowledge_space_id,
            len(codes),
            len(candidates),
        )
        return candidates

    async def _load_reachable_structure_rows(
        self,
        *,
        knowledge_space_id: UUID,
        base_filters,
    ):

        # Discovery needs field names, never the potentially huge JSON values.
        safe_data = case((func.jsonb_typeof(KnowledgeInformationModel.data) == 'object',
                          KnowledgeInformationModel.data), else_=func.jsonb_build_object())
        keys = func.jsonb_object_keys(safe_data).table_valued('key').render_derived()
        field_codes = select(func.array_agg(keys.c.key)).select_from(keys).correlate(KnowledgeInformationModel).scalar_subquery()
        result = await self.session.execute(
            select(
                KnowledgeInformationModel.information_type_id,
                KnowledgeInformationModel.object_refs,
                KnowledgeInformationModel.topic_refs,
                field_codes.label('field_codes'),
            ).distinct().where(
                KnowledgeInformationModel.knowledge_space_id
                == knowledge_space_id,
                or_(*base_filters),
            )
        )
        return result.all()

    async def _available_structure(self, *, knowledge_space_id, rows):
        return await ReachableStructureQuery(self.session).load(
            knowledge_space_id=knowledge_space_id,
            object_ids=self._object_ids_from_rows(rows),
            type_ids={row._mapping['information_type_id'] for row in rows
                      if row._mapping['information_type_id'] is not None},
            topic_codes=self._topic_codes_from_rows(rows),
            field_codes=self._field_codes_from_rows(rows),
        )

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
        started_at = perf_counter()
        logger.info(
            "[KNOWLEDGE_REPOSITORY] vector_code_search_start kind=%s space=%s top_k=%s",
            model_class.__tablename__,
            knowledge_space_id,
            top_k,
        )
        statement = (
            select(model_class).options(structure_options(model_class))
            .where(
                model_class.knowledge_space_id == knowledge_space_id,
                model_class.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )

        async def load():
            return (await self.session.execute(statement)).scalars().all()
        models = await vector_candidates((knowledge_space_id, model_class.__tablename__, 'embedding', tuple(vector), top_k), load)

        records = []
        for model in models:
            if model.code in seen:
                continue
            seen.add(model.code)
            records.append(record_factory(model))
        logger.info(
            "[KNOWLEDGE_REPOSITORY] vector_code_search kind=%s space=%s elapsed_ms=%s candidate_count=%s",
            model_class.__tablename__,
            knowledge_space_id,
            int((perf_counter() - started_at) * 1000),
            len(records),
        )
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
        started_at = perf_counter()
        logger.info(
            "[KNOWLEDGE_REPOSITORY] vector_object_search_start column=%s space=%s top_k=%s",
            getattr(column, "key", str(column)),
            knowledge_space_id,
            top_k,
        )
        statement = (
            select(KnowledgeObjectModel).options(structure_options(KnowledgeObjectModel))
            .where(
                KnowledgeObjectModel.knowledge_space_id
                == knowledge_space_id,
                column.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )

        async def load():
            return (await self.session.execute(statement)).scalars().all()
        models = await vector_candidates((knowledge_space_id, KnowledgeObjectModel.__tablename__, column.key, tuple(vector), top_k), load)

        records = []
        for model in models:
            key = (
                model.object_code,
                model.identifier_code,
            )
            if key in seen:
                continue
            seen.add(key)
            records.append(self._object_record(model))
        logger.info(
            "[KNOWLEDGE_REPOSITORY] vector_object_search column=%s space=%s elapsed_ms=%s candidate_count=%s",
            getattr(column, "key", str(column)),
            knowledge_space_id,
            int((perf_counter() - started_at) * 1000),
            len(records),
        )
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
        discovered_request: KnowledgeDiscoveredRequestRecord,
    ):

        return self._entry_point_filters_from_matches(
            knowledge_space_id=knowledge_space_id,
            matched_entry_points=discovered_request.matched_entry_points,
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
        type_codes = list(dict.fromkeys(item.code for item in matched_entry_points.information_types))
        if type_codes:
            filters.append(KnowledgeInformationModel.information_type_id.in_(
                select(KnowledgeInformationTypeModel.id).where(
                    KnowledgeInformationTypeModel.knowledge_space_id == knowledge_space_id,
                    KnowledgeInformationTypeModel.code.in_(type_codes),
                )
            ))
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
        filters.extend(
            KnowledgeInformationModel.data.has_key(field.code)
            for field in matched_entry_points.fields
        )
        return filters

    @staticmethod
    def _append_object_candidate(
        candidates: list[KnowledgeObjectStructureRecord],
        seen: set[tuple[str, str | None]],
        candidate: KnowledgeObjectStructureRecord,
    ) -> None:

        key = (
            candidate.object_code,
            candidate.identifier_code,
        )
        if key in seen:
            return
        seen.add(key)
        candidates.append(candidate)

    @staticmethod
    def _seed_values(
        request: dict[str, Any],
        key: str,
    ) -> list[str]:

        value = request.get(key)
        if value is None:
            return []
        if not isinstance(value, list):
            value = [
                value,
            ]

        result = []
        seen = set()
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

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
            if 'field_codes' in row._mapping:
                field_codes.update(row._mapping['field_codes'] or [])
                continue
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

    async def _upsert_by_space_code(
        self,
        *,
        model_class,
        values: dict[str, Any],
        merge_columns: list[str],
    ):

        statement = insert(model_class).values(**values)
        excluded = statement.excluded
        update_values = {}
        for column_name in merge_columns:
            column = getattr(model_class, column_name).property.columns[0]
            update_values[column] = func.coalesce(
                excluded[column.name],
                column,
            )
        update_values[model_class.updated_at.property.columns[0]] = func.now()

        statement = (
            statement.on_conflict_do_update(
                index_elements=[
                    model_class.knowledge_space_id,
                    model_class.code,
                ],
                set_=update_values,
            )
            .returning(model_class)
        )

        result = await self.session.execute(statement)
        model = result.scalar_one()
        await self.session.flush()
        return model

    async def _upsert_many_by_space_code(
        self,
        *,
        model_class,
        values: list[dict[str, Any]],
        merge_columns: list[str],
    ):
        statement = insert(model_class).values(values)
        excluded = statement.excluded
        update_values = {}
        for column_name in merge_columns:
            column = getattr(model_class, column_name).property.columns[0]
            update_values[column] = func.coalesce(
                excluded[column.name],
                column,
            )
        update_values[model_class.updated_at.property.columns[0]] = func.now()
        statement = (
            statement.on_conflict_do_update(
                index_elements=[
                    model_class.knowledge_space_id,
                    model_class.code,
                ],
                set_=update_values,
            )
            .returning(model_class)
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        return list(result.scalars().all())

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

    @staticmethod
    def _merge_aliases(existing, incoming):
        if incoming is None:
            return existing
        if existing is None:
            return deepcopy(incoming)
        if isinstance(existing, list) and isinstance(incoming, list):
            merged = deepcopy(existing)
            for value in incoming:
                if value not in merged:
                    merged.append(deepcopy(value))
            return merged
        if isinstance(existing, dict) and isinstance(incoming, dict):
            merged = deepcopy(existing)
            for key, value in incoming.items():
                if key not in merged:
                    merged[key] = deepcopy(value)
                elif isinstance(merged[key], list) and isinstance(value, list):
                    for item in value:
                        if item not in merged[key]:
                            merged[key].append(deepcopy(item))
            return merged
        return existing
