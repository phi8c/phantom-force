from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..enums.auth_provider import AuthProvider
from ..enums.authentication_context_type import AuthenticationContextType


@dataclass
class AuthSession:

    id: UUID

    user_id: UUID

    session_token_hash: str

    auth_method: AuthProvider

    context_type: AuthenticationContextType

    knowledge_space_id: UUID | None

    identity_link_id: UUID | None

    authenticated_at: datetime

    mfa_verified_at: datetime | None

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
        id: UUID,
        user_id: UUID,
        session_token_hash: str,
        auth_method: AuthProvider,
        ip_address: str | None,
        user_agent: str | None,
        device_fingerprint: str | None,
        now: datetime,
        idle_expires_at: datetime,
        absolute_expires_at: datetime,
        context_type: AuthenticationContextType,
        knowledge_space_id: UUID | None = None,
        identity_link_id: UUID | None = None,
        mfa_verified_at: datetime | None = None,
    ) -> AuthSession:
        """
        Session moi luon revoked_at=None, last_seen_at=issued_at=now - business
        rule nay thuoc domain, use case chi truyen input can thiet.
        """

        if (
            context_type is AuthenticationContextType.MANAGEMENT
            and knowledge_space_id is not None
        ):
            raise ValueError("Management sessions cannot be bound to a knowledge space")

        if (
            context_type is AuthenticationContextType.KNOWLEDGE_SPACE
            and knowledge_space_id is None
        ):
            raise ValueError("Knowledge Space sessions require a knowledge space")

        return cls(
            id=id,
            user_id=user_id,
            session_token_hash=session_token_hash,
            auth_method=auth_method,
            context_type=context_type,
            knowledge_space_id=knowledge_space_id,
            identity_link_id=identity_link_id,
            authenticated_at=now,
            mfa_verified_at=mfa_verified_at,
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
