from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class IngestionBatchModel(Base):
    __tablename__ = "ingestion_batches"

    __table_args__ = (
        UniqueConstraint(
            "ingestion_job_id",
            "batch_index",
            name="uq_ingestion_batches_job_index",
        ),
        UniqueConstraint(
            "id",
            "ingestion_job_id",
            name="uq_ingestion_batches_id_job",
        ),
        CheckConstraint(
            "batch_index > 0",
            name="ck_ingestion_batches_batch_index",
        ),
        CheckConstraint(
            "total_files >= 0",
            name="ck_ingestion_batches_total_files",
        ),
        CheckConstraint(
            "completed_files >= 0",
            name="ck_ingestion_batches_completed_files",
        ),
        CheckConstraint(
            "failed_files >= 0",
            name="ck_ingestion_batches_failed_files",
        ),
        CheckConstraint(
            "completed_files + failed_files <= total_files",
            name="ck_ingestion_batches_file_counts",
        ),
        CheckConstraint(
            "status IN "
            "('DISCOVERING', 'PROCESSING', 'COMPLETED', "
            "'COMPLETED_WITH_ERRORS', 'FAILED')",
            name="ck_ingestion_batches_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    ingestion_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="PROCESSING",
    )
    total_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    completed_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    failed_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    discovery_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
