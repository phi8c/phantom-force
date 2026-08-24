from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.role_source import RoleSource


@dataclass
class Role:

    id: str

    name: str

    description: str | None

    source: RoleSource

    external_role_value: str | None

    is_protected: bool

    created_by: str | None

    created_at: datetime

    updated_at: datetime