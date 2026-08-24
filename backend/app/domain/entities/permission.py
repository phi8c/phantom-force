from dataclasses import dataclass
from datetime import datetime


@dataclass
class Permission:

    id: str

    code: str

    resource_type: str

    action: str

    description: str | None

    created_at: datetime