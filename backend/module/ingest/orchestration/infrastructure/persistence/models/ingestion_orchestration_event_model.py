from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class IngestionOrchestrationEventModel(Base):
    __tablename__ = "ingestion_orchestration_events"

    __table_args__ = (
        UniqueConstraint(
            "sequence_no",
            name="uq_ingestion_orchestration_events_sequence",
        ),
        CheckConstraint(
            "stage IS NULL OR stage IN "
            "('DISCOVERY', 'DOWNLOAD', 'EXTRACTION', 'CHUNKING', "
            "'EMBEDDING', 'CLASSIFICATION', 'INDEXING')",
            name="ck_ingestion_orchestration_events_stage",
        ),
        CheckConstraint(
            "status IS NULL OR status IN "
            "('PENDING', 'READY', 'PROCESSING', 'COMPLETED', "
            "'FAILED', 'SKIPPED')",
            name="ck_ingestion_orchestration_events_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    sequence_no: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        nullable=False,
    )
    ingestion_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingestion_batch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ingestion_batches.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
