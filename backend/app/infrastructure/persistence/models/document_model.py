from datetime import datetime

from sqlalchemy import BigInteger

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class DocumentModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "documents"

    source_id: Mapped[str] = mapped_column(
        ForeignKey(
            "ingestion_sources.id",
        ),
        nullable=False,
    )

    
    file_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    owner_role: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    security_level: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    file_extension: Mapped[str | None] = mapped_column(
    String(20),
    nullable=True,
)

    file_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processing_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    

    source_file_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    
    provider_metadata: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
)

    external_file_id: Mapped[str] = mapped_column(
    Text,
)

    

    temp_file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    original_file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )