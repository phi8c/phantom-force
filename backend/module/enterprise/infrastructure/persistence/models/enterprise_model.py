from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)

    
class EnterpriseModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "enterprises"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
    )