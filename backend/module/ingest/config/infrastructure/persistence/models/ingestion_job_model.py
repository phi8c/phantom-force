from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from uuid import UUID

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class IngestionJobModel(
    Base,
    UUIDMixin,
):
    __tablename__ = "ingestion_jobs"

    knowledge_space_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    is_build_graph: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    total_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    scope_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    scope_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
