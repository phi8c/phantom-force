from sqlalchemy.dialects.postgresql import (
    UUID,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.shared.database.base import (
    Base,
)


class DocumentPipelineStateModel(
    Base,
):
    __tablename__ = (
        "document_pipeline_states"
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    chunks_ready: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    classification_ready: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    embedding_ready: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    index_event_published: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )