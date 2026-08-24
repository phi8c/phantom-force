from sqlalchemy import Boolean
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from uuid import UUID as PyUUID

from sqlalchemy.dialects.postgresql import UUID, JSONB



from app.shared.database.base import (
    Base,
    TimestampMixin,
)


class IngestionSourceModel(
    Base,
    TimestampMixin,
):
    __tablename__ = "ingestion_sources"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    source_type: Mapped[str] = mapped_column(
        String(50)
    )

  

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    provider_type: Mapped[str] = mapped_column(
    String(100)
    )

    provider_configuration: Mapped[dict] = mapped_column(
        JSONB
    )