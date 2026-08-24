from dataclasses import dataclass
from datetime import datetime


@dataclass
class PasswordHistory:

    id: str

    user_id: str

    password_hash: str

    created_at: datetime