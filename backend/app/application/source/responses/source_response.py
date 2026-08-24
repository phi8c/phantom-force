from dataclasses import dataclass
from uuid import UUID


@dataclass
class SourceResponse:
    id: UUID
    name: str
    source_type: str
    site_id: str
    enabled: bool