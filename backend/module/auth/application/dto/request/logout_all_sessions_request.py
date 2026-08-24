
from dataclasses import dataclass

from uuid import UUID
@dataclass
class LogoutAllSessionsRequest:

    user_id: UUID

    reason: str = "user_logout_all"