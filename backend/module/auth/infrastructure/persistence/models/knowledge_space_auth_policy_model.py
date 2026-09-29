from datetime import datetime
from uuid import UUID as PythonUUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base


class KnowledgeSpaceAuthPolicyModel(Base):
    __tablename__ = "knowledge_space_auth_policies"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_space_id",
            name="uq_knowledge_space_auth_policy",
        ),
        {"schema": "iam"},
    )

    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    knowledge_space_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    auth_method: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(255))
    require_mfa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idle_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    absolute_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("iam.users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
