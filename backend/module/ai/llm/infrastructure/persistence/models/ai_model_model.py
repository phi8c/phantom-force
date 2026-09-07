from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from uuid import UUID

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class AIModelModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "ai_models"
    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "code",
            name="ai_models_provider_id_code_key",
        ),
    )

    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "ai_providers.id",
        ),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    context_window: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    supports_stream: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    supports_json: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    supports_vision: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    supports_tools: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
