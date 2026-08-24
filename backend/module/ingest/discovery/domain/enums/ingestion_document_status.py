from enum import Enum


class IngestionDocumentStatus(
    str,
    Enum,
):
    PENDING = "PENDING"

    QUEUED = "QUEUED"

    PROCESSING = "PROCESSING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"