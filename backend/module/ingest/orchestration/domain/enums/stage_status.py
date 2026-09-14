from enum import Enum


class StageStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
