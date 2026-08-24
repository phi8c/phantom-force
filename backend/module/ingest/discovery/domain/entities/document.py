from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Document:
    id: UUID | None

    data_hub_id: UUID
    external_file_id: str

    file_name: str
    provider_metadata: dict | None

    source_file_url: str | None
    file_extension: str | None
    file_size_bytes: int | None
    original_file_path: str | None
    last_modified_at: datetime | None

    department: str | None
    owner_role: str | None
    security_level: str | None
    document_type: str | None

    created_at: datetime | None
    updated_at: datetime | None