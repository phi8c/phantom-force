from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class KnowledgeSpaceEmbeddingConfigModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = (
        "knowledge_space_embedding_configs"
    )

    knowledge_space_id: Mapped[str] = mapped_column(
        ForeignKey(
            "knowledge_spaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    embedding_model_id: Mapped[str] = mapped_column(
        ForeignKey(
            "embedding_models.id",
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