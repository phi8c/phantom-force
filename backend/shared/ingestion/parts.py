"""Manifest contracts for bounded extraction work; execution comes in phase 3."""
from dataclasses import dataclass
from enum import Enum


class PartStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ExtractionPart:
    id: str
    index: int
    status: PartStatus
    # Inclusive original PDF pages OR inclusive native DOCX block indices.
    source_start: int
    source_end: int
    artifact_path: str | None = None
    checksum: str | None = None
    attempts: int = 0
    error: str | None = None

    def __post_init__(self):
        if not self.id or self.index < 0 or self.attempts < 0:
            raise ValueError("Invalid part identity or attempts")
        if self.source_start < 0 or self.source_end < self.source_start:
            raise ValueError("Invalid inclusive source range")
        if self.status == PartStatus.COMPLETED and (
            not self.artifact_path or not self.checksum or self.error is not None
        ):
            raise ValueError("Completed part requires checksummed artifact and no error")
        if self.status == PartStatus.FAILED and not self.error:
            raise ValueError("Failed part requires error")


@dataclass(frozen=True)
class ExtractionManifest:
    document_id: str
    source_checksum: str
    configuration_fingerprint: str
    source_unit: str  # page or native_block
    parts: tuple[ExtractionPart, ...]
    schema_version: int = 2

    def __post_init__(self):
        if (self.schema_version != 2 or not self.document_id or not self.source_checksum
                or not self.configuration_fingerprint or not self.parts):
            raise ValueError("Manifest requires version, source/config identity and parts")
        if self.source_unit not in {"page", "native_block"}:
            raise ValueError("Unknown source unit")
        if len({part.id for part in self.parts}) != len(self.parts):
            raise ValueError("Duplicate part IDs")
        if tuple(part.index for part in self.parts) != tuple(range(len(self.parts))):
            raise ValueError("Parts must be ordered with contiguous zero-based indices")
        expected_start = 1 if self.source_unit == "page" else 0
        for part in self.parts:
            if part.source_start != expected_start:
                raise ValueError("Core source ranges must be contiguous without overlap")
            expected_start = part.source_end + 1

    @property
    def completed(self) -> bool:
        return all(part.status == PartStatus.COMPLETED for part in self.parts)
