from datetime import datetime
from uuid import UUID as PythonUUID, uuid4

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class AuthSessionModel(
    Base,
):

    __tablename__ = (
        "auth_sessions"
    )

    __table_args__ = (
        Index(
            "idx_auth_sessions_user",
            "user_id",
            postgresql_where="revoked_at is null",
        ),
        Index(
            "idx_auth_sessions_expiry",
            "idle_expires_at",
            postgresql_where="revoked_at is null",
        ),
        Index(
            "idx_auth_sessions_context",
            "context_type",
            "knowledge_space_id",
            postgresql_where="revoked_at is null",
        ),
        Index(
            "idx_auth_sessions_knowledge_space_user",
            "knowledge_space_id",
            "user_id",
            postgresql_where=(
                "context_type = 'KNOWLEDGE_SPACE' and revoked_at is null"
            ),
        ),
        Index(
            "idx_auth_sessions_identity_link",
            "identity_link_id",
            postgresql_where=(
                "identity_link_id is not null and revoked_at is null"
            ),
        ),
        CheckConstraint(
            "context_type in ('MANAGEMENT', 'KNOWLEDGE_SPACE')",
            name="ck_auth_sessions_context_type",
        ),
        CheckConstraint(
            "(context_type = 'MANAGEMENT' and knowledge_space_id is null) or "
            "(context_type = 'KNOWLEDGE_SPACE' and knowledge_space_id is not null)",
            name="ck_auth_sessions_context_scope",
        ),
        {"schema": "iam"},
    )

    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    session_token_hash: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    auth_method: Mapped[str] = mapped_column(
        Enum(
            "local",
            "entra",
            "google",
            name="auth_provider",
            schema="iam",
            create_type=False,
        ),
        nullable=False,
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

    issued_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    last_seen_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    idle_expires_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
            nullable=False,
        )
    )

    absolute_expires_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
            nullable=False,
        )
    )

    revoked_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )

    revoked_reason: Mapped[str | None] = mapped_column(
        String(64),
    )

    context_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    knowledge_space_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "knowledge_spaces.id",
            ondelete="CASCADE",
        ),
    )

    identity_link_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.identity_links.id",
            ondelete="SET NULL",
        ),
    )

    authenticated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    mfa_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
