from dataclasses import dataclass
from datetime import datetime


@dataclass
class MfaRecoveryCode:

    id: str

    user_id: str

    code_hash: str

    used_at: datetime | None

    created_at: datetime