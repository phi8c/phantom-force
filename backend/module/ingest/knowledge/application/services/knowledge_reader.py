import logging

from module.ingest.knowledge.application.dtos.knowledge_search_request import (
    KnowledgeSearchRequest,
)
from module.ingest.knowledge.application.dtos.knowledge_search_result import (
    KnowledgeSearchItem,
    KnowledgeSearchResult,
)
from module.ingest.knowledge.application.dtos.knowledge_discovery import (
    KnowledgeCodeStructure,
    KnowledgeDiscoveredSeed,
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
    KnowledgeDiscoveredSeedRecord,
    KnowledgeMatchedEntryPointsRecord,
    KnowledgeObjectStructureRecord,
)


logger = logging.getLogger(__name__)


class KnowledgeReader:

    def __init__(
        self,
        repository: KnowledgeRepository,
    ):
        self._repository = repository

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
            "[KNOWLEDGE_DISCOVERY] start space=%s seed_count=%s",
            request.knowledge_space_id,
            len(request.seeds),
        )

        records = await self._repository.discover(
            knowledge_space_id=request.knowledge_space_id,
            seeds=[
                {
                    "seed_id": seed.seed_id,
                    "object_code": seed.object_code,
                    "identifier_code": seed.identifier_code,
                    "information_type_code": (
                        seed.information_type_code
                    ),
                    "topic_codes": seed.topic_codes,
                    "constraints": seed.constraints,
                }
                for seed in request.seeds
            ],
        )

        seeds = [
            self._discovered_seed(record)
            for record in records
        ]
        requested_by_id = {
            seed.seed_id: seed
            for seed in request.seeds
        }

        for seed in seeds:
            requested = requested_by_id.get(seed.seed_id)
            logger.info(
                "[KNOWLEDGE_DISCOVERY] seed_id=%s "
                "requested_entry_points=%s "
                "matched_objects=%s matched_information_types=%s matched_topics=%s "
                "available_information_type_count=%s available_topic_count=%s "
                "available_field_count=%s",
                seed.seed_id,
                (
                    {
                        "object_code": requested.object_code,
                        "identifier_code": requested.identifier_code,
                        "information_type_code": (
                            requested.information_type_code
                        ),
                        "topic_codes": requested.topic_codes,
                    }
                    if requested is not None
                    else {}
                ),
                [
                    {
                        "object_code": item.object_code,
                        "identifier_code": item.identifier_code,
                    }
                    for item in seed.matched_entry_points.objects
                ],
                [
                    item.code
                    for item in (
                        seed.matched_entry_points.information_types
                    )
                ],
                [
                    item.code
                    for item in seed.matched_entry_points.topics
                ],
                len(seed.available_information_types),
                len(seed.available_topics),
                len(seed.available_fields),
            )

        return KnowledgeDiscoveryResult(
            seeds=seeds,
        )

    async def retrieve(
        self,
        request: KnowledgeRetrievalRequest,
    ) -> KnowledgeSearchResult:

        records = await self._repository.retrieve_for_selection(
            knowledge_space_id=request.knowledge_space_id,
            discovered_seed=self._discovered_seed_record(
                request.discovered_seed,
            ),
            information_type_codes=(
                request.selection.information_type_codes
            ),
            topic_codes=request.selection.topic_codes,
            field_codes=request.selection.field_codes,
        )

        logger.info(
            "[KNOWLEDGE_RETRIEVAL] selection=%s information_count=%s",
            {
                "seed_id": request.selection.seed_id,
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

    @classmethod
    def _discovered_seed(cls, record) -> KnowledgeDiscoveredSeed:

        return KnowledgeDiscoveredSeed(
            seed_id=record.seed_id,
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
            ),
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
    def _discovered_seed_record(
        cls,
        seed: KnowledgeDiscoveredSeed,
    ) -> KnowledgeDiscoveredSeedRecord:

        return KnowledgeDiscoveredSeedRecord(
            seed_id=seed.seed_id,
            matched_entry_points=KnowledgeMatchedEntryPointsRecord(
                objects=[
                    cls._object_structure_record(item)
                    for item in seed.matched_entry_points.objects
                ],
                information_types=[
                    cls._code_structure_record(item)
                    for item in (
                        seed
                        .matched_entry_points
                        .information_types
                    )
                ],
                topics=[
                    cls._code_structure_record(item)
                    for item in seed.matched_entry_points.topics
                ],
            ),
            available_objects=[
                cls._object_structure_record(item)
                for item in seed.available_objects
            ],
            available_information_types=[
                cls._code_structure_record(item)
                for item in seed.available_information_types
            ],
            available_topics=[
                cls._code_structure_record(item)
                for item in seed.available_topics
            ],
            available_fields=[
                cls._code_structure_record(item)
                for item in seed.available_fields
            ],
            constraints=seed.constraints,
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
