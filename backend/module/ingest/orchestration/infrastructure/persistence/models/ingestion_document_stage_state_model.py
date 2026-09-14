from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class IngestionDocumentStageStateModel(Base):
    __tablename__ = "ingestion_document_stage_states"

    __table_args__ = (
        ForeignKeyConstraint(
            [
                "ingestion_batch_id",
                "ingestion_job_id",
                "document_id",
            ],
            [
                "ingestion_batch_documents.ingestion_batch_id",
                "ingestion_batch_documents.ingestion_job_id",
                "ingestion_batch_documents.document_id",
            ],
            ondelete="CASCADE",
            name="fk_ingestion_document_stage_states_membership",
        ),
        UniqueConstraint(
            "ingestion_job_id",
            "document_id",
            "stage",
            name="uq_ingestion_document_stage_states_job_document_stage",
        ),
        CheckConstraint(
            "stage IN "
            "('DISCOVERY', 'DOWNLOAD', 'EXTRACTION', 'CHUNKING', "
            "'EMBEDDING', 'CLASSIFICATION', 'INDEXING')",
            name="ck_ingestion_document_stage_states_stage",
        ),
        CheckConstraint(
            "status IN "
            "('PENDING', 'READY', 'PROCESSING', 'COMPLETED', "
            "'FAILED', 'SKIPPED')",
            name="ck_ingestion_document_stage_states_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    ingestion_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    ingestion_batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="PENDING",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
