
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import DateTime

from app.shared.database.base import (
    Base,
    TimestampMixin,
)


class SyncStateModel(
    Base,
    TimestampMixin,
):
    __tablename__ = "sync_states"

    id: Mapped[str] = mapped_column(
        primary_key=True
    )

    source_id: Mapped[str] = mapped_column(
        ForeignKey(
            "ingestion_sources.id"
        )
    )

    delta_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    last_sync_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
)