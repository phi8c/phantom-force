from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database.base import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class DataHubProviderModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "data_hub_providers"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    configuration_schema: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )