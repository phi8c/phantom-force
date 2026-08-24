from dataclasses import dataclass
from datetime import datetime


@dataclass
class Credential:

    user_id: str

    password_hash: str

    password_algo: str

    password_changed_at: datetime

    failed_attempts: int

    locked_until: datetime | None

    mfa_enabled: bool

    mfa_secret_encrypted: str | None

    created_at: datetime

    updated_at: datetime