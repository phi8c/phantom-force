from uuid import uuid4

import pytest

from module.ingest.knowledge.domain.entities import (
    KnowledgeCodeStructureRecord,
    KnowledgeDiscoveredRequestRecord,
)
from module.ingest.knowledge.infrastructure.persistence.models import (
    KnowledgeInformationFieldModel,
    KnowledgeInformationTypeModel,
    KnowledgeTopicModel,
)
from module.ingest.knowledge.infrastructure.persistence.repositories.knowledge_repository_impl import (
    KnowledgeRepositoryImpl,
)


@pytest.mark.asyncio
async def test_discover_request_treats_topics_as_candidate_union():
    repository = RecordingKnowledgeRepository()
    knowledge_space_id = uuid4()

    record = await repository._discover_request(
        knowledge_space_id=knowledge_space_id,
        request={
            "request_id": "knowledge_1",
            "need": "Find requirements",
            "topic_seeds": [
                "topic_a",
                "topic_b",
            ],
            "document_type_seeds": [
                "missing_document_type",
            ],
        },
    )

    assert isinstance(record, KnowledgeDiscoveredRequestRecord)
    assert record.request_id == "knowledge_1"
    assert [
        item.code
        for item in record.matched_entry_points.topics
    ] == [
        "topic_a",
        "topic_b",
    ]
    assert repository.loaded_filter_count == 2
    assert repository.code_registry_calls == [
        (
            KnowledgeInformationTypeModel.__name__,
            [],
        ),
        (
            KnowledgeTopicModel.__name__,
            [
                "topic_a",
                "topic_b",
            ],
        ),
        (
            KnowledgeInformationFieldModel.__name__,
            [],
        ),
    ]


@pytest.mark.asyncio
async def test_discover_request_does_not_cartesian_product_dimensions():
    repository = RecordingKnowledgeRepository()

    await repository._discover_request(
        knowledge_space_id=uuid4(),
        request={
            "request_id": "knowledge_1",
            "topic_seeds": [
                "topic_a",
                "topic_b",
            ],
            "information_type_seeds": [
                "type_a",
                "type_b",
            ],
            "information_field_seeds": [
                "field_a",
                "field_b",
            ],
        },
    )

    assert repository.loaded_filter_count == 2
    assert repository.code_registry_calls == [
        (
            KnowledgeInformationTypeModel.__name__,
            [
                "type_a",
                "type_b",
            ],
        ),
        (
            KnowledgeTopicModel.__name__,
            [
                "topic_a",
                "topic_b",
            ],
        ),
        (
            KnowledgeInformationFieldModel.__name__,
            [
                "field_a",
                "field_b",
            ],
        ),
    ]


@pytest.mark.asyncio
async def test_discover_request_without_topic_uses_other_entry_points():
    repository = RecordingKnowledgeRepository()

    record = await repository._discover_request(
        knowledge_space_id=uuid4(),
        request={
            "request_id": "knowledge_1",
            "information_type_seeds": ["type_a"],
            "information_field_seeds": ["field_a"],
        },
    )

    assert record is not None
    assert repository.loaded_filter_count == 2


@pytest.mark.asyncio
async def test_discover_request_field_miss_does_not_kill_topic_candidate():
    repository = RecordingKnowledgeRepository(
        missing_codes={
            "missing_field",
        },
    )

    record = await repository._discover_request(
        knowledge_space_id=uuid4(),
        request={
            "request_id": "knowledge_1",
            "topic_seeds": [
                "topic_a",
            ],
            "information_field_seeds": [
                "missing_field",
            ],
        },
    )

    assert record is not None
    assert [
        item.code
        for item in record.matched_entry_points.topics
    ] == [
        "topic_a",
    ]
    assert record.matched_entry_points.fields == []
    assert repository.loaded_filter_count == 1


class RecordingKnowledgeRepository(KnowledgeRepositoryImpl):
    def __init__(self, missing_codes=None):
        super().__init__(session=None)
        self.code_registry_calls = []
        self.loaded_filter_count = None
        self.missing_codes = set(missing_codes or [])

    async def _match_objects_from_seeds(
        self,
        *,
        knowledge_space_id,
        object_codes,
        identifier_codes,
        object_vectors=None,
        identifier_vectors=None,
    ):
        return []

    async def _match_code_registry(
        self,
        *,
        model_class,
        record_factory,
        knowledge_space_id,
        codes,
        vectors=None,
    ):
        self.code_registry_calls.append(
            (
                model_class.__name__,
                list(codes),
            )
        )
        return [
            KnowledgeCodeStructureRecord(
                code=code,
                name=code,
                description=None,
            )
            for code in codes
            if code not in self.missing_codes
        ]

    async def _load_reachable_structure_rows(
        self,
        *,
        knowledge_space_id,
        base_filters,
    ):
        self.loaded_filter_count = len(base_filters)
        return []

    async def _available_objects(self, *, knowledge_space_id, rows):
        return []

    async def _available_information_types(
        self,
        *,
        knowledge_space_id,
        rows,
    ):
        return []

    async def _available_topics(self, *, knowledge_space_id, rows):
        return []

    async def _available_fields(self, *, knowledge_space_id, rows):
        return []
