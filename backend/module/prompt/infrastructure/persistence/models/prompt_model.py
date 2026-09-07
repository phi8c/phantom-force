from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class PromptModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "prompts"

    code: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
