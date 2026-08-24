from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class KnowledgeSpaceModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "knowledge_spaces"

    enterprise_id: Mapped[str] = mapped_column(
        ForeignKey(
            "enterprises.id",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )