from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Credential:

    user_id: UUID

    password_hash: str

    password_algo: str

    password_changed_at: datetime

    failed_attempts: int

    locked_until: datetime | None

    mfa_enabled: bool

    mfa_secret_encrypted: str | None

    created_at: datetime

    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: UUID,
        password_hash: str,
        password_algo: str,
        now: datetime,
    ) -> "Credential":
        return cls(
            user_id=user_id,
            password_hash=password_hash,
            password_algo=password_algo,
            password_changed_at=now,
            failed_attempts=0,
            locked_until=None,
            mfa_enabled=False,
            mfa_secret_encrypted=None,
            created_at=now,
            updated_at=now,
        )
