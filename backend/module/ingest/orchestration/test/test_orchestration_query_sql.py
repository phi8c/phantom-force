from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from module.ingest.orchestration.infrastructure.persistence.queries import (
    OrchestrationQueryService,
)


@pytest.mark.asyncio
async def test_events_query_reads_only_sequence_after_cursor():
    session = RecordingSession()
    service = OrchestrationQueryService(
        session=session,
    )

    await service.list_events_after(
        ingestion_job_id=uuid4(),
        after=42,
    )

    sql = compile_postgresql(
        session.statement,
    )

    assert "ingestion_orchestration_events.sequence_no >" in sql
    assert "ORDER BY ingestion_orchestration_events.sequence_no ASC" in sql


@pytest.mark.asyncio
async def test_batch_detail_query_filters_job_and_batch():
    session = RecordingSession()
    service = OrchestrationQueryService(
        session=session,
    )

    await service.list_batch_documents(
        ingestion_job_id=uuid4(),
        ingestion_batch_id=uuid4(),
    )

    sql = compile_postgresql(
        session.statement,
    )

    assert "ingestion_batch_documents.ingestion_job_id =" in sql
    assert "ingestion_batch_documents.ingestion_batch_id =" in sql
    assert "JOIN documents" in sql


class RecordingSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


class EmptyResult:
    def all(self):
        return []

    def scalars(self):
        return self


def compile_postgresql(statement):
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={
                "literal_binds": False,
            },
        )
    )
