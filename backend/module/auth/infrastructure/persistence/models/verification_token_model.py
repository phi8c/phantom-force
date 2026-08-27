from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class VerificationTokenModel(
    Base,
):

    __tablename__ = (
        "verification_tokens"
    )

    __table_args__ = (
        Index(
            "idx_verification_tokens_user",
            "user_id",
            "purpose",
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

    token_hash: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        Enum(
            "email_verify",
            "password_reset",
            name="token_purpose",
            schema="iam",
            create_type=False,
        ),
        nullable=False,
    )

    expires_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
            nullable=False,
        )
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