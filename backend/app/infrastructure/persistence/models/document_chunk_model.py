from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class DocumentChunkModel(
    Base,
):

    __tablename__ = (
        "document_chunks"
    )

    __table_args__ = (
        Index(
            "idx_document_chunks_batch",
            "batch_id",
        ),
        Index(
            "idx_document_chunks_document",
            "document_id",
        ),
    
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_chunk_batches.id",
        ),
        nullable=False,
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
        ),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_payload: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True,
        ),
    )