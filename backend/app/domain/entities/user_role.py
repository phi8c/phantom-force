from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.role_assignment_source import RoleAssignmentSource


@dataclass
class UserRole:

    user_id: str

    role_id: str

    source: RoleAssignmentSource

    assigned_by: str | None

    assigned_at: datetime