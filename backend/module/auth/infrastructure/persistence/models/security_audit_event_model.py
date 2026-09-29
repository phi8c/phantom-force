from datetime import datetime
from typing import Any
from uuid import UUID as PythonUUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base


class SecurityAuditEventModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"schema": "iam"},)

    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    actor_user_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("iam.users.id"),
    )
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(100))
    target_id: Mapped[PythonUUID | None] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255))
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
