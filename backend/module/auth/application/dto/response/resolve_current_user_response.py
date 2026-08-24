from dataclasses import dataclass
from uuid import UUID


@dataclass
class ResolveCurrentUserResult:

    user_id: UUID

    email: str

    session_id: UUID