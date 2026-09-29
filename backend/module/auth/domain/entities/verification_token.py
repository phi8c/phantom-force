from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from module.auth.domain.enums.token_purpose import TokenPurpose


@dataclass
class VerificationToken:
    id: UUID
    user_id: UUID

    token_hash: str

    purpose: TokenPurpose

    expires_at: datetime

    used_at: datetime | None

    created_at: datetime

    @classmethod
    def create_for_purpose(
        cls,
        id: UUID,
        user_id: UUID,
        token_hash: str,
        purpose: TokenPurpose,
        now: datetime,
        ttl: timedelta,
    ) -> "VerificationToken":
        if ttl <= timedelta(0):
            raise ValueError("Verification token TTL must be positive")
        return cls(
            id=id,
            user_id=user_id,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=now + ttl,
            used_at=None,
            created_at=now,
        )

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now

    def is_used(self) -> bool:
        return self.used_at is not None

    def consume(self, now: datetime) -> None:
        if self.is_used():
            raise ValueError("Verification token has already been used")
        if self.is_expired(now):
            raise ValueError("Verification token has expired")
        self.used_at = now
