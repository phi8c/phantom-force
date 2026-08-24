# app/domain/entities/document_image.py

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DocumentImage:

    id: UUID | None

    document_id: UUID

    page_number: int

    asset_url: str

    description: str | None

    created_at: datetime | None