from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base, TimestampMixin, UUIDMixin


class KnowledgeSpaceQueueModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "knowledge_space_queues"

    knowledge_space_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "knowledge_spaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    queue_provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("queue_providers.id"),
        nullable=False,
    )
    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    is_default: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
