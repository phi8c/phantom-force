from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class AuditLogModel(
    Base,
):

    __tablename__ = (
        "audit_logs"
    )

    __table_args__ = (
        Index(
            "idx_audit_logs_occurred",
            "occurred_at",
        ),
        Index(
            "idx_audit_logs_actor",
            "actor_user_id",
        ),
        {"schema": "iam"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    actor_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
        ),
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(100),
    )

    target_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
    )

    device_fingerprint: Mapped[str | None] = mapped_column(
        String(255),
    )

    # "metadata" la thuoc tinh reserved cua SQLAlchemy Base (MetaData object),
    # nen dat ten attribute Python la metadata_payload nhung van map dung cot
    # "metadata" o DB qua tham so dau tien cua mapped_column.
    metadata_payload: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
    )

    occurred_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )   