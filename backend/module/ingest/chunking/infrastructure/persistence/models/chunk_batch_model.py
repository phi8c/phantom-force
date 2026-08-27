from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class ChunkBatchModel(
    Base,
):
    __tablename__ = "document_chunk_batches"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "batch_index",
            name=(
                "document_chunk_batches_"
                "document_id_batch_index_key"
            ),
        ),
        Index(
            "idx_chunk_batches_document",
            "document_id",
        ),
        Index(
            "idx_chunk_batches_ingestion_job",
            "ingestion_job_id",
        ),
        Index(
            "uq_document_chunk_batches_job_document",
            "ingestion_job_id",
            "document_id",
            unique=True,
            postgresql_where=(
                text(
                    "ingestion_job_id IS NOT NULL"
                )
            ),
        ),
        {
            "extend_existing": True,
        },
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    batch_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    classification_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    embedding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    batch_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    ingestion_job_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "ingestion_jobs.id",
            ondelete="CASCADE",
            name=(
                "fk_document_chunk_batches_"
                "ingestion_job"
            ),
        ),
        nullable=True,
    )
