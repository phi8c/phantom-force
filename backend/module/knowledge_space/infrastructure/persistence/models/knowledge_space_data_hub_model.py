from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class KnowledgeSpaceDataHubModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "knowledge_space_data_hubs"

    knowledge_space_id: Mapped[str] = mapped_column(
        ForeignKey(
            "knowledge_spaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    data_hub_provider_id: Mapped[str] = mapped_column(
        ForeignKey(
            "data_hub_providers.id",
        ),
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