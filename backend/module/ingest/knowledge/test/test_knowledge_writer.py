from uuid import uuid4
from pathlib import Path

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


def test_knowledge_does_not_import_config_infrastructure():
    root = Path(__file__).parents[1]
    content = "\n".join(
        path.read_text()
        for path in root.rglob("*.py")
        if "test" not in path.parts
    )

    assert "module.ingest.config.infrastructure" not in content
    assert "IngestionJobModel" not in content


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
    updated["information_types"][0]["description"] = "Updated"
    await writer.write(request(raw_response=updated))

    entity = repo.information_types[("space", "technical_specification")]
    assert entity.description == "Updated"


@pytest.mark.asyncio
async def test_registry_update_does_not_overwrite_with_null():
    repo = FakeKnowledgeRepository()
    writer = KnowledgeWriter(repo)

    await writer.write(request(raw_response=sample_response()))
    updated = sample_response()
    updated["information_types"][0]["description"] = None
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
    raw["objects"].append(
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
            "model_name": write_request.model_name,
            "ordinal": 0,
            "confidence": 0.9,
        }
    ]


@pytest.mark.asyncio
async def test_retry_same_chunk_output_does_not_duplicate_information():
    repo = FakeKnowledgeRepository()
    write_request = request(raw_response=sample_response())
    writer = KnowledgeWriter(repo)

    await writer.write(write_request)
    await writer.write(write_request)

    assert len(repo.information) == 1


@pytest.mark.asyncio
async def test_same_chunk_multiple_information_items_are_preserved():
    repo = FakeKnowledgeRepository()
    raw = sample_response()
    raw["information"].append(
        {
            "information_type": "technical_specification",
            "summary": "Product A switching force is 2450 N.",
            "data": {
                "switching_force": {
                    "value": 2450,
                    "unit": "N",
                }
            },
            "object_refs": ["product_a"],
            "topic_refs": ["railway_safety"],
            "confidence": 0.8,
        }
    )

    await KnowledgeWriter(repo).write(
        request(raw_response=raw),
    )

    assert len(repo.information) == 2


@pytest.mark.asyncio
async def test_malformed_response_contract_fails_clearly():
    repo = FakeKnowledgeRepository()
    raw = sample_response()
    raw.pop("document_type")

    with pytest.raises(
        ValueError,
        match="Knowledge response missing document_type",
    ):
        await KnowledgeWriter(repo).write(
            request(raw_response=raw),
        )


@pytest.mark.asyncio
async def test_classification_passes_knowledge_space_id_to_write_request():
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
    writer = RecordingKnowledgeWriter()
    classification_repository = FakeClassificationRepository()
    use_case = ClassifyBatchUseCase(
        task_repository=FakeTaskRepository(task),
        chunk_reader=FakeChunkReader(),
        classification_engine=FakeClassificationEngine(),
        classification_repository=classification_repository,
        batch_finalizer=SuccessfulBatchFinalizer(),
        knowledge_writer=writer,
        ingestion_config_service=FakeIngestionConfigService(),
        uow=FakeUow(),
    )

    await use_case.execute(task.id)

    assert writer.requests[0].knowledge_space_id == "space"
    assert classification_repository.classifications[0].label == "2"
    assert classification_repository.classifications[0].confidence is None


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
        ingestion_config_service=FakeIngestionConfigService(),
        uow=uow,
    )

    with pytest.raises(RuntimeError):
        await use_case.execute(task.id)

    assert uow.rolled_back is True


def request(raw_response):
    return KnowledgeWriteRequest(
        knowledge_space_id="space",
        document_id=uuid4(),
        chunk_id=uuid4(),
        model_name="gpt-test",
        raw_response=raw_response,
    )


def sample_response():
    return {
        "sensitivity": {
            "level": 2,
            "description": "Internal technical information.",
        },
        "document_type": {
            "code": "technical_document",
            "name": "Technical document",
        },
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
                "information_type": "technical_specification",
                "summary": "Product A voltage is 160 V.",
                "data": {
                    "voltage": {
                        "value": 160,
                        "unit": "V",
                    }
                },
                "object_refs": ["product_a"],
                "topic_refs": ["railway_safety"],
                "confidence": 0.9,
            }
        ],
    }


class FakeKnowledgeRepository:
    def __init__(self):
        self.document_types = {}
        self.information_types = {}
        self.fields = {}
        self.objects = {}
        self.topics = {}
        self.information = []

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

    async def upsert_information(self, entity, source_identity):
        for existing in self.information:
            if source_identity.items() <= existing.source_refs[0].items():
                existing.information_type_id = entity.information_type_id
                existing.summary = entity.summary
                existing.data = entity.data
                existing.object_refs = entity.object_refs
                existing.topic_refs = entity.topic_refs
                existing.source_refs = entity.source_refs
                existing.confidence = entity.confidence
                existing.raw_model_output = entity.raw_model_output
                existing.metadata = entity.metadata
                return existing
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
                raw_response=sample_response(),
            )
        ]


class FakeClassificationRepository:
    def __init__(self):
        self.classifications = []

    async def upsert_many(self, classifications):
        self.classifications = list(classifications)
        return self.classifications


class FakeBatchFinalizer:
    async def complete_classification(self, ingestion_job_id, batch_id):
        raise AssertionError("finalizer should not run")


class SuccessfulBatchFinalizer:
    async def complete_classification(self, ingestion_job_id, batch_id):
        return SuccessfulBatchSignal()

    async def dispatch_index(self, ingestion_job_id):
        pass


class SuccessfulBatchSignal:
    dispatch_index = False


class RecordingKnowledgeWriter:
    def __init__(self):
        self.requests = []

    async def write(self, request):
        self.requests.append(request)


class FailingKnowledgeWriter:
    async def write(self, request):
        raise RuntimeError("knowledge failed")


class FakeIngestionConfigService:
    async def get_job(self, job_id):
        return FakeIngestionJob()


class FakeIngestionJob:
    knowledge_space_id = "space"


class FakeUow:
    def __init__(self):
        self.rolled_back = False

    async def commit(self):
        pass

    async def rollback(self):
        self.rolled_back = True
