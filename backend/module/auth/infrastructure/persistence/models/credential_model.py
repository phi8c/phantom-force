from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import SmallInteger
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class CredentialModel(
    Base,
):

    __tablename__ = (
        "credentials"
    )

    __table_args__ = (
        {"schema": "iam"}
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    password_algo: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="argon2id",
    )

    password_changed_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    failed_attempts: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
    )

    locked_until: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    mfa_secret_encrypted: Mapped[str | None] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )