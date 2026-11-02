from pathlib import Path
from typing import Protocol

from shared.ingestion.parts import ExtractionManifest, ExtractionPart


class PartExecutionError(RuntimeError):
    def __init__(self, message: str, *, can_split: bool = True, retryable: bool = True):
        super().__init__(message)
        self.can_split = can_split
        self.retryable = retryable


class PartExecutor(Protocol):
    async def execute(self, source: Path, destination: Path) -> None:
        """Return only after a bounded part has produced a complete V2 artifact."""
        ...


class ExtractionCheckpointStore(Protocol):
    def load(self) -> ExtractionManifest | None:
        ...

    def save(self, manifest: ExtractionManifest) -> None:
        ...

    def verified_artifact(self, part: ExtractionPart) -> bool:
        ...
