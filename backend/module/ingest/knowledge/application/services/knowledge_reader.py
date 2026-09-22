import logging
from collections.abc import Awaitable
from collections.abc import Callable
from time import perf_counter
from uuid import UUID
from shared.logging.chat_diagnostics import print_chat_trace

from module.ingest.knowledge.application.dtos.knowledge_search_request import (
    KnowledgeSearchRequest,
)
from module.ingest.knowledge.application.dtos.knowledge_search_result import (
    KnowledgeSearchItem,
    KnowledgeSearchResult,
)
from module.ingest.knowledge.application.dtos.knowledge_discovery import (
    KnowledgeCodeStructure,
    KnowledgeDiscoveredRequest,
    KnowledgeDiscoveryRequest,
    KnowledgeDiscoveryResult,
    KnowledgeMatchedEntryPoints,
    KnowledgeObjectStructure,
    KnowledgeRetrievalRequest,
)
from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeCodeStructureRecord,
    KnowledgeDiscoveredRequestRecord,
    KnowledgeMatchedEntryPointsRecord,
    KnowledgeObjectStructureRecord,
    KnowledgeSemanticRequestVectors,
)
from module.ingest.embedding.domain.contracts.text_embedding_provider import (
    TextEmbeddingProvider,
)


logger = logging.getLogger(__name__)


class KnowledgeReader:

    def __init__(
        self,
        repository: KnowledgeRepository,
        embedder_factory: Callable[
            [UUID],
            Awaitable[TextEmbeddingProvider],
        ] | None = None,
    ):
        self._repository = repository
        self._embedder_factory = embedder_factory

    async def search_information(
        self,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResult:

        logger.info(
            "[KNOWLEDGE_READER] search "
            "space=%s object=%s identifier=%s information_type=%s topics=%s",
            request.knowledge_space_id,
            request.object_code,
            request.identifier_code,
            request.information_type_code,
            request.topic_codes,
        )

        records = await self._repository.search_information(
            knowledge_space_id=request.knowledge_space_id,
            object_code=request.object_code,
            identifier_code=request.identifier_code,
            information_type_code=request.information_type_code,
            topic_codes=request.topic_codes,
        )

        logger.info(
            "[KNOWLEDGE_READER] repository returned count=%s",
            len(records),
        )

        return KnowledgeSearchResult(
            items=[
                KnowledgeSearchItem(
                    information_id=record.information_id,
                    information_type_code=record.information_type_code,
                    summary=record.summary,
                    data=record.data,
                    object_refs=record.object_refs or [],
                    topic_refs=record.topic_refs or [],
                    source_refs=record.source_refs or [],
                    confidence=record.confidence,
                )
                for record in records
            ],
        )

    async def discover(
        self,
        request: KnowledgeDiscoveryRequest,
    ) -> KnowledgeDiscoveryResult:

        logger.info(
            "[KNOWLEDGE_DISCOVERY] start space=%s request_count=%s",
            request.knowledge_space_id,
            len(request.items),
        )

        request_vectors = await self._embed_seed_strings(
            request,
        )
        print_chat_trace("SEED_VECTORS_BY_REQUEST", request_vectors)

        records = await self._repository.discover(
            knowledge_space_id=request.knowledge_space_id,
            requests=[
                {
                    "request_id": item.request_id,
                    "need": item.need,
                    "document_type_seeds": (
                        item.document_type_seeds
                    ),
                    "head_seeds": item.head_seeds,
                    "topic_seeds": item.topic_seeds,
                    "object_seeds": item.object_seeds,
                    "identifier_seeds": item.identifier_seeds,
                    "information_type_seeds": (
                        item.information_type_seeds
                    ),
                    "information_field_seeds": (
                        item.information_field_seeds
                    ),
                    "constraints": item.constraints,
                }
                for item in request.items
            ],
            request_vectors=request_vectors,
        )
        print_chat_trace("DISCOVERY_REPOSITORY_RECORDS", records)

        discovered_requests = [
            self._discovered_request(record)
            for record in records
        ]
        requested_by_id = {
            item.request_id: item
            for item in request.items
        }

        for discovered_request in discovered_requests:
            requested = requested_by_id.get(
                discovered_request.request_id,
            )
            logger.info(
                "[KNOWLEDGE_DISCOVERY] request_id=%s need=%s "
                "requested_semantic_seeds=%s "
                "matched_objects=%s matched_information_types=%s matched_topics=%s matched_fields=%s "
                "available_information_type_count=%s available_topic_count=%s "
                "available_field_count=%s",
                discovered_request.request_id,
                discovered_request.need,
                (
                    {
                        "document_type_seeds": (
                            requested.document_type_seeds
                        ),
                        "head_seeds": requested.head_seeds,
                        "topic_seeds": requested.topic_seeds,
                        "object_seeds": requested.object_seeds,
                        "identifier_seeds": requested.identifier_seeds,
                        "information_type_seeds": (
                            requested.information_type_seeds
                        ),
                        "information_field_seeds": (
                            requested.information_field_seeds
                        ),
                    }
                    if requested is not None
                    else {}
                ),
                [
                    {
                        "object_code": item.object_code,
                        "identifier_code": item.identifier_code,
                    }
                    for item in (
                        discovered_request.matched_entry_points.objects
                    )
                ],
                [
                    item.code
                    for item in (
                        discovered_request
                        .matched_entry_points
                        .information_types
                    )
                ],
                [
                    item.code
                    for item in discovered_request.matched_entry_points.topics
                ],
                [
                    item.code
                    for item in discovered_request.matched_entry_points.fields
                ],
                len(discovered_request.available_information_types),
                len(discovered_request.available_topics),
                len(discovered_request.available_fields),
            )

        return KnowledgeDiscoveryResult(
            requests=discovered_requests,
        )

    async def retrieve(
        self,
        request: KnowledgeRetrievalRequest,
    ) -> KnowledgeSearchResult:

        records = await self._repository.retrieve_for_selection(
            knowledge_space_id=request.knowledge_space_id,
            discovered_request=self._discovered_request_record(
                request.discovered_request,
            ),
            information_type_codes=(
                request.selection.information_type_codes
            ),
            topic_codes=request.selection.topic_codes,
            field_codes=request.selection.field_codes,
        )
        print_chat_trace("RETRIEVAL_REPOSITORY_RECORDS", records)

        logger.info(
            "[KNOWLEDGE_RETRIEVAL] selection=%s information_count=%s",
            {
                "request_id": request.selection.request_id,
                "information_type_codes": (
                    request.selection.information_type_codes
                ),
                "topic_codes": request.selection.topic_codes,
                "field_codes": request.selection.field_codes,
            },
            len(records),
        )

        return KnowledgeSearchResult(
            items=[
                KnowledgeSearchItem(
                    information_id=record.information_id,
                    information_type_code=record.information_type_code,
                    summary=record.summary,
                    data=record.data,
                    object_refs=record.object_refs or [],
                    topic_refs=record.topic_refs or [],
                    source_refs=record.source_refs or [],
                    confidence=record.confidence,
                )
                for record in records
            ],
        )

    async def _embed_seed_strings(
        self,
        request: KnowledgeDiscoveryRequest,
    ) -> list[KnowledgeSemanticRequestVectors] | None:

        if self._embedder_factory is None:
            return None

        started_at = perf_counter()
        texts = []
        for item in request.items:
            texts.extend(item.document_type_seeds)
            texts.extend(item.topic_seeds)
            texts.extend(item.object_seeds)
            texts.extend(item.identifier_seeds)
            texts.extend(item.information_type_seeds)
            texts.extend(item.information_field_seeds)

        unique_texts = list(dict.fromkeys(texts))
        print_chat_trace("SEED_EMBEDDING_INPUT", {
            "knowledge_space_id": request.knowledge_space_id,
            "texts": texts,
            "unique_texts": unique_texts,
        })
        if not unique_texts:
            return []

        logger.info(
            "[KNOWLEDGE_DISCOVERY] seed_embedding_start space=%s input_count=%s unique_count=%s",
            request.knowledge_space_id,
            len(texts),
            len(unique_texts),
        )
        embedder = await self._embedder_factory(
            request.knowledge_space_id,
        )
        vectors = await embedder.embed_texts(unique_texts)
        print_chat_trace("SEED_EMBEDDING_OUTPUT", [
            {"seed": text, "vector": vector}
            for text, vector in zip(unique_texts, vectors, strict=True)
        ])
        vector_by_text = dict(
            zip(unique_texts, vectors, strict=True),
        )

        logger.info(
            "[KNOWLEDGE_DISCOVERY] embedded_seeds space=%s input_count=%s unique_count=%s",
            request.knowledge_space_id,
            len(texts),
            len(unique_texts),
        )
        logger.info(
            "[KNOWLEDGE_DISCOVERY] seed_embedding_done space=%s elapsed_ms=%s",
            request.knowledge_space_id,
            int((perf_counter() - started_at) * 1000),
        )

        return [
            KnowledgeSemanticRequestVectors(
                request_id=item.request_id,
                document_type_vectors=self._vectors_for_texts(
                    item.document_type_seeds,
                    vector_by_text,
                ),
                topic_vectors={
                    topic_code: vector_by_text[topic_code]
                    for topic_code in item.topic_seeds
                    if topic_code in vector_by_text
                },
                object_vectors=self._vectors_for_texts(
                    item.object_seeds,
                    vector_by_text,
                ),
                identifier_vectors=self._vectors_for_texts(
                    item.identifier_seeds,
                    vector_by_text,
                ),
                information_type_vectors=self._vectors_for_texts(
                    item.information_type_seeds,
                    vector_by_text,
                ),
                information_field_vectors=self._vectors_for_texts(
                    item.information_field_seeds,
                    vector_by_text,
                ),
            )
            for item in request.items
        ]

    @staticmethod
    def _vectors_for_texts(
        texts: list[str],
        vector_by_text: dict[str, list[float]],
    ) -> dict[str, list[float]]:

        return {
            text: vector_by_text[text]
            for text in texts
            if text in vector_by_text
        }

    @classmethod
    def _discovered_request(cls, record) -> KnowledgeDiscoveredRequest:

        return KnowledgeDiscoveredRequest(
            request_id=record.request_id,
            matched_entry_points=KnowledgeMatchedEntryPoints(
                objects=[
                    cls._object_structure(item)
                    for item in record.matched_entry_points.objects
                ],
                information_types=[
                    cls._code_structure(item)
                    for item in (
                        record
                        .matched_entry_points
                        .information_types
                    )
                ],
                topics=[
                    cls._code_structure(item)
                    for item in record.matched_entry_points.topics
                ],
                fields=[
                    cls._code_structure(item)
                    for item in record.matched_entry_points.fields
                ],
            ),
            need=getattr(record, "need", ""),
            original_seeds=getattr(record, "original_seeds", {}),
            available_objects=[
                cls._object_structure(item)
                for item in record.available_objects
            ],
            available_information_types=[
                cls._code_structure(item)
                for item in record.available_information_types
            ],
            available_topics=[
                cls._code_structure(item)
                for item in record.available_topics
            ],
            available_fields=[
                cls._code_structure(item)
                for item in record.available_fields
            ],
            constraints=record.constraints,
        )

    @staticmethod
    def _object_structure(record) -> KnowledgeObjectStructure:

        return KnowledgeObjectStructure(
            object_code=record.object_code,
            identifier_code=record.identifier_code,
            name=record.name,
            identifier_name=record.identifier_name,
            description=record.description,
        )

    @staticmethod
    def _code_structure(record) -> KnowledgeCodeStructure:

        return KnowledgeCodeStructure(
            code=record.code,
            name=record.name,
            description=record.description,
            data_type=record.data_type,
        )

    @classmethod
    def _discovered_request_record(
        cls,
        request: KnowledgeDiscoveredRequest,
    ) -> KnowledgeDiscoveredRequestRecord:

        return KnowledgeDiscoveredRequestRecord(
            request_id=request.request_id,
            matched_entry_points=KnowledgeMatchedEntryPointsRecord(
                objects=[
                    cls._object_structure_record(item)
                    for item in request.matched_entry_points.objects
                ],
                information_types=[
                    cls._code_structure_record(item)
                    for item in (
                        request
                        .matched_entry_points
                        .information_types
                    )
                ],
                topics=[
                    cls._code_structure_record(item)
                    for item in request.matched_entry_points.topics
                ],
                fields=[
                    cls._code_structure_record(item)
                    for item in request.matched_entry_points.fields
                ],
            ),
            need=request.need,
            original_seeds=request.original_seeds,
            available_objects=[
                cls._object_structure_record(item)
                for item in request.available_objects
            ],
            available_information_types=[
                cls._code_structure_record(item)
                for item in request.available_information_types
            ],
            available_topics=[
                cls._code_structure_record(item)
                for item in request.available_topics
            ],
            available_fields=[
                cls._code_structure_record(item)
                for item in request.available_fields
            ],
            constraints=request.constraints,
        )

    @staticmethod
    def _object_structure_record(
        item: KnowledgeObjectStructure,
    ) -> KnowledgeObjectStructureRecord:

        return KnowledgeObjectStructureRecord(
            object_code=item.object_code,
            identifier_code=item.identifier_code,
            name=item.name,
            identifier_name=item.identifier_name,
            description=item.description,
        )

    @staticmethod
    def _code_structure_record(
        item: KnowledgeCodeStructure,
    ) -> KnowledgeCodeStructureRecord:

        return KnowledgeCodeStructureRecord(
            code=item.code,
            name=item.name,
            description=item.description,
            data_type=item.data_type,
        )
