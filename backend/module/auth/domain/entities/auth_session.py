from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..enums.auth_provider import AuthProvider


@dataclass
class AuthSession:

    id: str

    user_id: str

    session_token_hash: str

    auth_method: AuthProvider

    ip_address: str | None

    user_agent: str | None

    device_fingerprint: str | None

    issued_at: datetime

    last_seen_at: datetime

    idle_expires_at: datetime

    absolute_expires_at: datetime

    revoked_at: datetime | None

    revoked_reason: str | None

    @classmethod
    def create(
        cls,
        id: str,
        user_id: str,
        session_token_hash: str,
        auth_method: AuthProvider,
        ip_address: str | None,
        user_agent: str | None,
        device_fingerprint: str | None,
        now: datetime,
        idle_expires_at: datetime,
        absolute_expires_at: datetime,
    ) -> AuthSession:
        """
        Session moi luon revoked_at=None, last_seen_at=issued_at=now - business
        rule nay thuoc domain, use case chi truyen input can thiet.
        """

        return cls(
            id=id,
            user_id=user_id,
            session_token_hash=session_token_hash,
            auth_method=auth_method,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            issued_at=now,
            last_seen_at=now,
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
            revoked_at=None,
            revoked_reason=None,
        )