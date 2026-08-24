from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base

from sqlalchemy.dialects.postgresql import (
    JSONB,
)


class DocumentExtractionModel(
    Base,
):

    __tablename__ = (
        "document_extractions"
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
        ),
    )

    structured_content: Mapped[dict] = (
    mapped_column(
        JSONB,
    )
)

    page_count: Mapped[int | None] = (
        mapped_column(
            Integer,
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )