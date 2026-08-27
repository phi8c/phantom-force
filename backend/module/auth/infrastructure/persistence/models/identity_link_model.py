from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class IdentityLinkModel(
    Base,
):

    __tablename__ = (
        "identity_links"
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_sub",
            name="uq_identity_links_provider_sub",
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

    provider: Mapped[str] = mapped_column(
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

    external_sub: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    tenant_id: Mapped[str | None] = mapped_column(
        String(255),
    )

    email_at_link: Mapped[str] = mapped_column(
        CITEXT,
        nullable=False,
    )

    linked_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True,
            ),
        )
    )