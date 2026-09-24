from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base, TimestampMixin, UUIDMixin


class QueueProviderModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "queue_providers"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
