from uuid import uuid4

import pytest

from module.ingest.classification.application.use_cases.classify_batch import (
    ClassifyBatchUseCase,
)
from module.ingest.classification.domain.contracts.classification_engine import (
    ClassificationResult,
)
from module.ingest.classification.domain.entities.classification_task import (
    ClassificationTask,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.knowledge.application.dtos import (
    KnowledgeWriteRequest,
)
from module.ingest.knowledge.application.services.knowledge_writer import (
    KnowledgeWriter,
)


@pytest.mark.asyncio
async def test_registry_insert():
    repo = FakeKnowledgeRepository()
    writer = KnowledgeWriter(repo)

    await writer.write(request(raw_response=sample_response()))

    assert repo.information_types[("space", "technical_specification")].name == "Technical specification"
    assert repo.information[0].summary == "Product A voltage is 160 V."


@pytest.mark.asyncio
async def test_registry_update():
    repo = FakeKnowledgeRepository()
    writer = KnowledgeWriter(repo)

    await writer.write(request(raw_response=sample_response()))
    updated = sample_response()
    updated["structured_knowledge"]["information_types"][0]["description"] = "Updated"
    await writer.write(request(raw_response=updated))

    entity = repo.information_types[("space", "technical_specification")]
    assert entity.description == "Updated"


@pytest.mark.asyncio
async def test_registry_update_does_not_overwrite_with_null():
    repo = FakeKnowledgeRepository()
    writer = KnowledgeWriter(repo)

    await writer.write(request(raw_response=sample_response()))
    updated = sample_response()
    updated["structured_knowledge"]["information_types"][0]["description"] = None
    await writer.write(request(raw_response=updated))

    entity = repo.information_types[("space", "technical_specification")]
    assert entity.description == "Initial"


@pytest.mark.asyncio
async def test_object_with_identifier():
    repo = FakeKnowledgeRepository()
    writer = KnowledgeWriter(repo)

    await writer.write(request(raw_response=sample_response()))

    assert ("space", "product", "product_a") in repo.objects


@pytest.mark.asyncio
async def test_object_without_identifier():
    repo = FakeKnowledgeRepository()
    raw = sample_response()
    raw["structured_knowledge"]["objects"].append(
        {
            "object_code": "market",
            "identifier_code": None,
            "object_name": "Market",
        }
    )

    await KnowledgeWriter(repo).write(request(raw_response=raw))

    assert ("space", "market", None) in repo.objects


@pytest.mark.asyncio
async def test_information_type_resolution():
    repo = FakeKnowledgeRepository()

    await KnowledgeWriter(repo).write(request(raw_response=sample_response()))

    information = repo.information[0]
    resolved_type = repo.information_types[("space", "technical_specification")]
    assert information.information_type_id == resolved_type.id


@pytest.mark.asyncio
async def test_field_registry():
    repo = FakeKnowledgeRepository()

    await KnowledgeWriter(repo).write(request(raw_response=sample_response()))

    field = repo.fields[("space", "voltage")]
    assert field.data_type == "measurement"
    assert field.unit_type == "voltage"


@pytest.mark.asyncio
async def test_topic_resolution():
    repo = FakeKnowledgeRepository()

    await KnowledgeWriter(repo).write(request(raw_response=sample_response()))

    topic_refs = repo.information[0].topic_refs
    assert topic_refs[0]["code"] == "railway_safety"
    assert "topic_id" in topic_refs[0]


@pytest.mark.asyncio
async def test_provenance_source_refs():
    repo = FakeKnowledgeRepository()
    write_request = request(raw_response=sample_response())

    await KnowledgeWriter(repo).write(write_request)

    source_refs = repo.information[0].source_refs
    assert source_refs == [
        {
            "document_id": str(write_request.document_id),
            "chunk_id": str(write_request.chunk_id),
            "confidence": 0.9,
        }
    ]


@pytest.mark.asyncio
async def test_transaction_rollback_when_knowledge_persistence_fails():
    task = ClassificationTask(
        id=uuid4(),
        ingestion_job_id=uuid4(),
        batch_id=uuid4(),
        document_id=uuid4(),
        status=TaskStatus.PROCESSING,
        attempt_count=1,
        claimed_by=None,
        lease_until=None,
        error=None,
        created_at=None,
        updated_at=None,
        completed_at=None,
    )
    uow = FakeUow()
    use_case = ClassifyBatchUseCase(
        task_repository=FakeTaskRepository(task),
        chunk_reader=FakeChunkReader(),
        classification_engine=FakeClassificationEngine(),
        classification_repository=FakeClassificationRepository(),
        batch_finalizer=FakeBatchFinalizer(),
        knowledge_writer=FailingKnowledgeWriter(),
        uow=uow,
    )

    with pytest.raises(RuntimeError):
        await use_case.execute(task.id)

    assert uow.rolled_back is True


def request(raw_response):
    return KnowledgeWriteRequest(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
        chunk_id=uuid4(),
        model_name="gpt-test",
        raw_response=raw_response,
    )


def sample_response():
    return {
        "classification": {
            "label": "internal",
            "confidence": 0.9,
        },
        "structured_knowledge": {
            "document_types": [
                {
                    "code": "technical_document",
                    "name": "Technical document",
                }
            ],
            "information_types": [
                {
                    "code": "technical_specification",
                    "name": "Technical specification",
                    "description": "Initial",
                }
            ],
            "information_fields": [
                {
                    "code": "voltage",
                    "data_type": "measurement",
                    "unit_type": "voltage",
                }
            ],
            "objects": [
                {
                    "object_code": "product",
                    "identifier_code": "product_a",
                    "object_name": "Product",
                    "identifier_name": "Product A",
                }
            ],
            "topics": [
                {
                    "code": "railway_safety",
                    "name": "Railway safety",
                }
            ],
            "information": [
                {
                    "information_type_code": "technical_specification",
                    "summary": "Product A voltage is 160 V.",
                    "data": {
                        "voltage": {
                            "value": 160,
                            "unit": "V",
                        }
                    },
                    "object_refs": [
                        {
                            "object_code": "product",
                            "identifier_code": "product_a",
                        }
                    ],
                    "topic_refs": [
                        {
                            "code": "railway_safety",
                        }
                    ],
                    "confidence": 0.9,
                }
            ],
        },
    }


class FakeKnowledgeRepository:
    def __init__(self):
        self.document_types = {}
        self.information_types = {}
        self.fields = {}
        self.objects = {}
        self.topics = {}
        self.information = []

    async def get_knowledge_space_id_by_job_id(self, ingestion_job_id):
        return "space"

    async def upsert_document_type(self, entity):
        return self._upsert(self.document_types, ("space", entity.code), entity)

    async def upsert_information_type(self, entity):
        return self._upsert(self.information_types, ("space", entity.code), entity)

    async def upsert_information_field(self, entity):
        return self._upsert(self.fields, ("space", entity.code), entity)

    async def upsert_object(self, entity):
        key = ("space", entity.object_code, entity.identifier_code)
        return self._upsert(self.objects, key, entity)

    async def upsert_topic(self, entity):
        return self._upsert(self.topics, ("space", entity.code), entity)

    async def add_information(self, entity):
        entity.id = uuid4()
        self.information.append(entity)
        return entity

    @staticmethod
    def _upsert(store, key, entity):
        existing = store.get(key)
        if existing is None:
            entity.id = uuid4()
            store[key] = entity
            return entity
        for name, value in entity.__dict__.items():
            if value is not None:
                setattr(existing, name, value)
        return existing


class FakeTaskRepository:
    def __init__(self, task):
        self.task = task

    async def get_by_id(self, task_id):
        return self.task

    async def update(self, task):
        self.task = task
        return task


class FakeChunkReader:
    async def list_by_batch_id(self, batch_id):
        return []


class FakeClassificationEngine:
    async def classify_batch(self, chunks):
        return [
            ClassificationResult(
                chunk_id=uuid4(),
                model_name="model",
                raw_response={
                    "classification": {
                        "label": "internal",
                    }
                },
            )
        ]


class FakeClassificationRepository:
    async def upsert_many(self, classifications):
        return list(classifications)


class FakeBatchFinalizer:
    async def complete_classification(self, ingestion_job_id, batch_id):
        raise AssertionError("finalizer should not run")


class FailingKnowledgeWriter:
    async def write(self, request):
        raise RuntimeError("knowledge failed")


class FakeUow:
    def __init__(self):
        self.rolled_back = False

    async def commit(self):
        pass

    async def rollback(self):
        self.rolled_back = True
