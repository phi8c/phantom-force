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


class RefreshTokenModel(
    Base,
):

    __tablename__ = (
        "refresh_tokens"
    )

    __table_args__ = (
        Index(
            "idx_refresh_tokens_session",
            "session_id",
        ),
        {"schema": "iam"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.auth_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    issued_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
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

    revoked_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    replaced_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.refresh_tokens.id",
        ),
    )