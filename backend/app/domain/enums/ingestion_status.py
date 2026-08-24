from enum import Enum


class IngestionStatus(
    str,
    Enum,
):
    PENDING = "PENDING"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"