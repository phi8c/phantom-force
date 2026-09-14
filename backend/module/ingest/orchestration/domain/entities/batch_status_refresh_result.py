from dataclasses import dataclass

from module.ingest.orchestration.domain.enums import BatchStatus


@dataclass(frozen=True)
class BatchStatusRefreshResult:
    status: BatchStatus
    changed: bool
