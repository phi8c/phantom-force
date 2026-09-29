from datetime import datetime
from uuid import UUID as PythonUUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base


class ManagementAuthPolicyModel(Base):
    __tablename__ = "management_auth_policy"
    __table_args__ = ({"schema": "iam"},)

    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    auth_method: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(255))
    require_mfa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    idle_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    absolute_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reauthentication_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
