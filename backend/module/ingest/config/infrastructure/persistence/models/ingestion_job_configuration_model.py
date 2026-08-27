from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class IngestionJobConfigurationModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "ingestion_job_configurations"

    ingestion_job_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    is_classification: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    model_set_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    chunking_strategy_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    extraction_engine_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )