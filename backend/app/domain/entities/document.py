from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Document:

    id: UUID | None

    source_id: UUID

    external_file_id: str

    provider_metadata: dict | None

    file_name: str

    department: str | None

    owner_role: str | None

    security_level: str | None

    document_type: str | None

    source_file_url: str | None

    file_extension: str | None

    file_size_bytes: int | None

    content_hash: str | None

    processing_status: str | None

    processing_error: str | None

    temp_file_path: str | None
    
    original_file_path: str | None 

    last_modified_at: datetime | None

    last_ingested_at: datetime | None

    created_at: datetime | None

    updated_at: datetime | None