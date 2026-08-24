from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import (
    Base,
)


class IngestJobModel(
    Base,
):
    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(
        primary_key=True
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey(
            "documents.id"
        )
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    error_message: Mapped[str | None] = mapped_column(
        Text
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )