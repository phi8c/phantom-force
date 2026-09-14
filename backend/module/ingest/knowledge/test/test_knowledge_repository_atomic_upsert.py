from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformationField,
    KnowledgeInformationType,
    KnowledgeTopic,
)
from module.ingest.knowledge.infrastructure.persistence.repositories.knowledge_repository_impl import (
    KnowledgeRepositoryImpl,
)


@pytest.mark.asyncio
async def test_information_field_upsert_uses_postgresql_on_conflict():
    session = RecordingSession(
        result_model=information_field_model(
            knowledge_space_id=uuid4(),
            code="amount",
            name="Amount",
            description="Payment amount",
            data_type="number",
            unit_type="usd",
            metadata_payload={
                "source": "classification",
            },
        ),
    )
    repository = KnowledgeRepositoryImpl(session)

    await repository.upsert_information_field(
        KnowledgeInformationField(
            id=None,
            knowledge_space_id=uuid4(),
            code="amount",
            name="Amount",
            description="Payment amount",
            data_type="number",
            unit_type="usd",
            metadata={
                "source": "classification",
            },
            created_at=None,
            updated_at=None,
        )
    )

    sql = compile_postgresql(session.statement)

    assert "ON CONFLICT (knowledge_space_id, code) DO UPDATE" in sql
    assert "name = coalesce(excluded.name, knowledge_information_fields.name)" in sql
    assert (
        "description = coalesce(excluded.description, "
        "knowledge_information_fields.description)"
    ) in sql
    assert (
        "data_type = coalesce(excluded.data_type, "
        "knowledge_information_fields.data_type)"
    ) in sql
    assert (
        "unit_type = coalesce(excluded.unit_type, "
        "knowledge_information_fields.unit_type)"
    ) in sql
    assert (
        "metadata = coalesce(excluded.metadata, "
        "knowledge_information_fields.metadata)"
    ) in sql
    assert "updated_at = now()" in sql
    assert "RETURNING" in sql


@pytest.mark.asyncio
async def test_information_field_upsert_returns_returned_row():
    knowledge_space_id = uuid4()
    session = RecordingSession(
        result_model=information_field_model(
            knowledge_space_id=knowledge_space_id,
            code="amount",
            name="Amount",
            description="Payment amount",
            data_type="number",
            unit_type="usd",
            metadata_payload={
                "source": "classification",
            },
        ),
    )
    repository = KnowledgeRepositoryImpl(session)

    result = await repository.upsert_information_field(
        KnowledgeInformationField(
            id=None,
            knowledge_space_id=knowledge_space_id,
            code="amount",
            name=None,
            description=None,
            data_type=None,
            unit_type=None,
            metadata=None,
            created_at=None,
            updated_at=None,
        )
    )

    assert result.knowledge_space_id == knowledge_space_id
    assert result.code == "amount"
    assert result.name == "Amount"
    assert result.description == "Payment amount"
    assert result.data_type == "number"
    assert result.unit_type == "usd"
    assert result.metadata == {
        "source": "classification",
    }
    assert session.flush_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "entity", "result_model"),
    [
        (
            "upsert_document_type",
            KnowledgeDocumentType(
                id=None,
                knowledge_space_id=uuid4(),
                code="project_plan",
                name="Project plan",
                description=None,
                structuring_guidance=None,
                metadata=None,
                created_at=None,
                updated_at=None,
            ),
            document_type_model,
        ),
        (
            "upsert_information_type",
            KnowledgeInformationType(
                id=None,
                knowledge_space_id=uuid4(),
                code="requirement",
                name="Requirement",
                description=None,
                metadata=None,
                created_at=None,
                updated_at=None,
            ),
            information_type_model,
        ),
        (
            "upsert_topic",
            KnowledgeTopic(
                id=None,
                knowledge_space_id=uuid4(),
                code="deployment",
                name="Deployment",
                description=None,
                metadata=None,
                created_at=None,
                updated_at=None,
            ),
            topic_model,
        ),
    ],
)
async def test_space_code_registry_upserts_use_same_atomic_conflict_target(
    method_name,
    entity,
    result_model,
):
    session = RecordingSession(
        result_model=result_model(
            knowledge_space_id=entity.knowledge_space_id,
            code=entity.code,
            name=entity.name,
        ),
    )
    repository = KnowledgeRepositoryImpl(session)

    await getattr(repository, method_name)(entity)

    sql = compile_postgresql(session.statement)
    assert "ON CONFLICT (knowledge_space_id, code) DO UPDATE" in sql
    assert "RETURNING" in sql


class RecordingSession:
    def __init__(self, *, result_model):
        self._result_model = result_model
        self.statement = None
        self.flush_count = 0

    async def execute(self, statement):
        self.statement = statement
        return RecordingResult(self._result_model)

    async def flush(self):
        self.flush_count += 1


class RecordingResult:
    def __init__(self, model):
        self._model = model

    def scalar_one(self):
        return self._model


def compile_postgresql(statement):
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={
                "literal_binds": False,
            },
        )
    )


def information_field_model(
    *,
    knowledge_space_id,
    code,
    name,
    description,
    data_type,
    unit_type,
    metadata_payload,
):
    return type(
        "InformationFieldModel",
        (),
        {
            "id": uuid4(),
            "knowledge_space_id": knowledge_space_id,
            "code": code,
            "name": name,
            "description": description,
            "data_type": data_type,
            "unit_type": unit_type,
            "metadata_payload": metadata_payload,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
        },
    )()


def document_type_model(*, knowledge_space_id, code, name):
    return type(
        "DocumentTypeModel",
        (),
        {
            "id": uuid4(),
            "knowledge_space_id": knowledge_space_id,
            "code": code,
            "name": name,
            "description": None,
            "structuring_guidance": None,
            "metadata_payload": None,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
        },
    )()


def information_type_model(*, knowledge_space_id, code, name):
    return type(
        "InformationTypeModel",
        (),
        {
            "id": uuid4(),
            "knowledge_space_id": knowledge_space_id,
            "code": code,
            "name": name,
            "description": None,
            "metadata_payload": None,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
        },
    )()


def topic_model(*, knowledge_space_id, code, name):
    return type(
        "TopicModel",
        (),
        {
            "id": uuid4(),
            "knowledge_space_id": knowledge_space_id,
            "code": code,
            "name": name,
            "description": None,
            "metadata_payload": None,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
        },
    )()
