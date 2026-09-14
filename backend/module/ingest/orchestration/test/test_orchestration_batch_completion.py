from uuid import uuid4

from module.ingest.orchestration.domain.enums import BatchStatus
from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.orchestration.domain.enums import StageStatus
from module.ingest.orchestration.infrastructure.persistence.repositories.orchestration_repository_impl import (
    OrchestrationRepositoryImpl,
)


REQUIRED_STAGES = {
    IngestionStage.DISCOVERY.value,
    IngestionStage.DOWNLOAD.value,
    IngestionStage.EXTRACTION.value,
    IngestionStage.CHUNKING.value,
    IngestionStage.EMBEDDING.value,
    IngestionStage.CLASSIFICATION.value,
}


def test_failed_terminal_file_does_not_keep_batch_processing():
    completed_files, failed_files, status = (
        OrchestrationRepositoryImpl
        ._summarize_batch_completion(
            total_files=2,
            required_stages=REQUIRED_STAGES,
            states_by_document={
                uuid4(): {
                    stage: StageStatus.COMPLETED.value
                    for stage in REQUIRED_STAGES
                },
                uuid4(): {
                    IngestionStage.DISCOVERY.value: (
                        StageStatus.COMPLETED.value
                    ),
                    IngestionStage.DOWNLOAD.value: (
                        StageStatus.FAILED.value
                    ),
                },
            },
        )
    )

    assert completed_files == 1
    assert failed_files == 1
    assert status == BatchStatus.COMPLETED_WITH_ERRORS


def test_classification_skipped_satisfies_required_stage():
    states = {
        stage: StageStatus.COMPLETED.value
        for stage in REQUIRED_STAGES
    }
    states[IngestionStage.CLASSIFICATION.value] = (
        StageStatus.SKIPPED.value
    )

    completed_files, failed_files, status = (
        OrchestrationRepositoryImpl
        ._summarize_batch_completion(
            total_files=1,
            required_stages=REQUIRED_STAGES,
            states_by_document={
                uuid4(): states,
            },
        )
    )

    assert completed_files == 1
    assert failed_files == 0
    assert status == BatchStatus.COMPLETED


def test_incomplete_file_keeps_batch_processing():
    completed_files, failed_files, status = (
        OrchestrationRepositoryImpl
        ._summarize_batch_completion(
            total_files=1,
            required_stages=REQUIRED_STAGES,
            states_by_document={
                uuid4(): {
                    IngestionStage.DISCOVERY.value: (
                        StageStatus.COMPLETED.value
                    ),
                    IngestionStage.DOWNLOAD.value: (
                        StageStatus.PROCESSING.value
                    ),
                },
            },
        )
    )

    assert completed_files == 0
    assert failed_files == 0
    assert status == BatchStatus.PROCESSING
