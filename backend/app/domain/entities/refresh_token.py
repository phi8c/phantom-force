from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:

    id: str

    session_id: str

    token_hash: str

    issued_at: datetime

    expires_at: datetime

    used_at: datetime | None

    revoked_at: datetime | None

    replaced_by: str | None