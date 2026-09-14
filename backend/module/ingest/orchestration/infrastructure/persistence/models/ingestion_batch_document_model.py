from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class IngestionBatchDocumentModel(Base):
    __tablename__ = "ingestion_batch_documents"

    __table_args__ = (
        ForeignKeyConstraint(
            ["ingestion_batch_id", "ingestion_job_id"],
            ["ingestion_batches.id", "ingestion_batches.ingestion_job_id"],
            ondelete="CASCADE",
            name="fk_ingestion_batch_documents_batch_job",
        ),
        UniqueConstraint(
            "ingestion_batch_id",
            "document_id",
            name="uq_ingestion_batch_documents_batch_document",
        ),
        UniqueConstraint(
            "ingestion_job_id",
            "document_id",
            name="uq_ingestion_batch_documents_job_document",
        ),
        UniqueConstraint(
            "ingestion_batch_id",
            "ingestion_job_id",
            "document_id",
            name="uq_ingestion_batch_documents_membership",
        ),
        CheckConstraint(
            "ordinal IS NULL OR ordinal >= 0",
            name="ck_ingestion_batch_documents_ordinal",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    ingestion_batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    ingestion_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
