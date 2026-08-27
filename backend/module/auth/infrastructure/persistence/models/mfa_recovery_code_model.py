from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class MfaRecoveryCodeModel(
    Base,
):

    __tablename__ = (
        "mfa_recovery_codes"
    )

    __table_args__ = (
        Index(
            "idx_mfa_recovery_codes_user",
            "user_id",
            postgresql_where="used_at is null",
        ),
        {"schema": "iam"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    code_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    used_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )