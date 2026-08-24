from uuid import uuid4

from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import Base


class PolicyConditionModel(
    Base,
):

    __tablename__ = (
        "policy_conditions"
    )

    __table_args__ = (
        Index(
            "idx_policy_conditions_policy",
            "policy_id",
        ),
        {"schema": "iam"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    policy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "iam.policies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    attribute_path: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    operator: Mapped[str] = mapped_column(
        Enum(
            "eq",
            "neq",
            "in",
            "gte",
            "lte",
            "contains",
            name="policy_operator",
            schema="iam",
            create_type=False,
        ),
        nullable=False,
    )

    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )