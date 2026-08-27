from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Chunk:
    document_id: UUID
    source_section_id: str
    sequence: int
    title: str | None
    content: str
    hierarchy_path: list[str]
    level: int
    tables: list[str]
    image_captions: list[str]
    metadata: dict
