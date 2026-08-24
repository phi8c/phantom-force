from sqlalchemy import ForeignKey

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class RolePermissionModel(
    Base,
):

    __tablename__ = (
        "role_permissions"
    )

    __table_args__ = (
        {"schema": "iam"}
    )

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    permission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )