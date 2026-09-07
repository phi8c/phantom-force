from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class AIProviderModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "ai_providers"

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    base_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    api_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
