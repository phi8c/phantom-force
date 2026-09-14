from uuid import uuid4

import pytest

from module.ingest.orchestration.application.services import (
    OrchestrationProgressService,
)
from module.ingest.orchestration.domain.entities import (
    BatchStatusRefreshResult,
    DiscoveryBatchCreationResult,
)
from module.ingest.orchestration.domain.enums import BatchStatus
from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.orchestration.domain.enums import OrchestrationEventType
from module.ingest.orchestration.domain.enums import StageStatus


@pytest.mark.asyncio
async def test_discovery_creates_batch_stage_states_and_events():
    repository = RecordingOrchestrationRepository()
    service = OrchestrationProgressService(
        repository=repository,
    )
    job_id = uuid4()
    document_ids = [
        uuid4()
        for _ in range(10)
    ]

    batch_id = await service.create_discovery_batch(
        ingestion_job_id=job_id,
        document_ids=document_ids,
    )

    assert batch_id == repository.batch_id
    assert repository.created_batches == [
        (
            job_id,
            document_ids,
        )
    ]
    assert len(repository.stage_states) == 20
    assert all(
        (
            job_id,
            repository.batch_id,
            document_id,
            IngestionStage.DISCOVERY,
            StageStatus.COMPLETED,
            None,
        )
        in repository.stage_states
        for document_id in document_ids
    )
    assert all(
        (
            job_id,
            repository.batch_id,
            document_id,
            IngestionStage.DOWNLOAD,
            StageStatus.READY,
            None,
        )
        in repository.stage_states
        for document_id in document_ids
    )
    assert [
        event["event_type"]
        for event in repository.events
    ].count(
        OrchestrationEventType.BATCH_CREATED,
    ) == 1


@pytest.mark.asyncio
async def test_discovery_retry_does_not_duplicate_events():
    repository = RecordingOrchestrationRepository(
        discovery_created=False,
    )
    service = OrchestrationProgressService(
        repository=repository,
    )

    batch_id = await service.create_discovery_batch(
        ingestion_job_id=uuid4(),
        document_ids=[
            uuid4(),
        ],
    )

    assert batch_id == repository.batch_id
    assert repository.events == []


@pytest.mark.asyncio
async def test_file_can_advance_while_other_file_stays_processing():
    repository = RecordingOrchestrationRepository()
    service = OrchestrationProgressService(
        repository=repository,
    )
    job_id = uuid4()
    document_a_id = uuid4()
    document_b_id = uuid4()

    await service.mark_stage_completed(
        ingestion_job_id=job_id,
        document_id=document_a_id,
        stage=IngestionStage.DOWNLOAD,
    )
    await service.mark_stage_processing(
        ingestion_job_id=job_id,
        document_id=document_a_id,
        stage=IngestionStage.EXTRACTION,
    )
    await service.mark_stage_processing(
        ingestion_job_id=job_id,
        document_id=document_b_id,
        stage=IngestionStage.DOWNLOAD,
    )

    assert repository.latest_status(
        document_a_id,
        IngestionStage.EXTRACTION,
    ) == StageStatus.PROCESSING
    assert repository.latest_status(
        document_b_id,
        IngestionStage.DOWNLOAD,
    ) == StageStatus.PROCESSING


@pytest.mark.asyncio
async def test_retryable_failure_marks_stage_ready_not_failed():
    repository = RecordingOrchestrationRepository()
    service = OrchestrationProgressService(
        repository=repository,
    )
    document_id = uuid4()

    await service.mark_stage_ready(
        ingestion_job_id=uuid4(),
        document_id=document_id,
        stage=IngestionStage.DOWNLOAD,
    )

    assert repository.latest_status(
        document_id,
        IngestionStage.DOWNLOAD,
    ) == StageStatus.READY
    assert all(
        event["status"] != StageStatus.FAILED
        for event in repository.events
    )


@pytest.mark.asyncio
async def test_classification_skipped_can_complete_batch():
    repository = RecordingOrchestrationRepository(
        refresh_result=BatchStatusRefreshResult(
            status=BatchStatus.COMPLETED,
            changed=True,
        ),
    )
    service = OrchestrationProgressService(
        repository=repository,
    )

    await service.mark_stage_skipped(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
        stage=IngestionStage.CLASSIFICATION,
    )

    assert repository.events[-2]["event_type"] == (
        OrchestrationEventType.DOCUMENT_STAGE_SKIPPED
    )
    assert repository.events[-1]["event_type"] == (
        OrchestrationEventType.BATCH_COMPLETED
    )
    assert repository.events[-1]["payload"] == {
        "status": BatchStatus.COMPLETED.value,
    }


class RecordingOrchestrationRepository:
    def __init__(
        self,
        *,
        discovery_created=True,
        refresh_result=None,
    ):
        self.batch_id = uuid4()
        self.discovery_created = discovery_created
        self.refresh_result = refresh_result or BatchStatusRefreshResult(
            status=BatchStatus.PROCESSING,
            changed=False,
        )
        self.created_batches = []
        self.stage_states = []
        self.events = []

    async def create_discovery_batch(
        self,
        *,
        ingestion_job_id,
        document_ids,
    ):
        self.created_batches.append(
            (
                ingestion_job_id,
                document_ids,
            )
        )
        if self.discovery_created:
            for document_id in document_ids:
                self.stage_states.append(
                    (
                        ingestion_job_id,
                        self.batch_id,
                        document_id,
                        IngestionStage.DISCOVERY,
                        StageStatus.COMPLETED,
                        None,
                    )
                )
                self.stage_states.append(
                    (
                        ingestion_job_id,
                        self.batch_id,
                        document_id,
                        IngestionStage.DOWNLOAD,
                        StageStatus.READY,
                        None,
                    )
                )
        return DiscoveryBatchCreationResult(
            ingestion_batch_id=self.batch_id,
            created=self.discovery_created,
        )

    async def find_batch_id_for_document(
        self,
        *,
        ingestion_job_id,
        document_id,
    ):
        return self.batch_id

    async def upsert_stage_state(
        self,
        *,
        ingestion_job_id,
        ingestion_batch_id,
        document_id,
        stage,
        status,
        error=None,
    ):
        self.stage_states.append(
            (
                ingestion_job_id,
                ingestion_batch_id,
                document_id,
                stage,
                status,
                error,
            )
        )

    async def refresh_batch_status(
        self,
        *,
        ingestion_batch_id,
    ):
        return self.refresh_result

    async def append_event(
        self,
        *,
        ingestion_job_id,
        event_type,
        ingestion_batch_id=None,
        document_id=None,
        stage=None,
        status=None,
        payload=None,
    ):
        self.events.append(
            {
                "ingestion_job_id": ingestion_job_id,
                "event_type": event_type,
                "ingestion_batch_id": ingestion_batch_id,
                "document_id": document_id,
                "stage": stage,
                "status": status,
                "payload": payload or {},
            }
        )

    def latest_status(
        self,
        document_id,
        stage,
    ):
        for state in reversed(self.stage_states):
            if (
                state[2] == document_id
                and state[3] == stage
            ):
                return state[4]
        return None
