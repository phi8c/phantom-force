from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy import JSON

from sqlalchemy.dialects.postgresql import UUID, JSONB  

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base





class IngestionRunModel(Base):

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ingestion_sources.id"
        ),
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
    )

    status: Mapped[str] = mapped_column(
        String(50),
    )

    is_build_graph: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    total_files: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completed_files: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    failed_files: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    
    configuration: Mapped[dict] = mapped_column(
    JSON,
    nullable=False,
    default=dict,
)
    
    
    scope_type: Mapped[str] = mapped_column(
        String(50),
    )

   

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
)
    scope_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
)