from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.policy_effect import PolicyEffect


@dataclass
class Policy:

    id: str

    name: str

    effect: PolicyEffect

    resource_type: str

    action: str

    priority: int

    is_active: bool

    created_by: str | None

    created_at: datetime

    updated_at: datetime