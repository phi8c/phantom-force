from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class UserRoleModel(
    Base,
):

    __tablename__ = (
        "user_roles"
    )

    __table_args__ = (
        Index(
            "idx_user_roles_user",
            "user_id",
        ),
        {"schema": "iam"},
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    source: Mapped[str] = mapped_column(
        Enum(
            "manual",
            "entra_sync",
            name="role_assignment_source",
            schema="iam",
            create_type=False,
        ),
        nullable=False,
        default="manual",
    )

    assigned_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
        ),
    )

    assigned_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )