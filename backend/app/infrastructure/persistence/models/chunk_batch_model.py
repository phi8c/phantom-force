from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class ChunkBatchModel(
    Base,
):

    __tablename__ = (
        "document_chunk_batches"
    )

    __table_args__ = (
    Index(
        "idx_chunk_batch_document",
        "document_id",
    ),
   
)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
        ),
        nullable=False,
    )

    batch_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    total_chunks: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
)
    
    classification_completed: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
)

    embedding_completed: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
)

    batch_completed: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
)
  

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True,
        ),
    )