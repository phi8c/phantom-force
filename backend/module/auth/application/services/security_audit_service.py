from typing import Any
from uuid import UUID, uuid4

from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.security_audit_repository import (
    SecurityAuditRepository,
)
from module.auth.domain.entities.security_audit_event import SecurityAuditEvent


class SecurityAuditService:
    def __init__(self, repository: SecurityAuditRepository, clock: Clock):
        self._repository = repository
        self._clock = clock

    async def record(
        self,
        action: str,
        *,
        actor_user_id: UUID | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_fingerprint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._repository.add(
            SecurityAuditEvent(
                id=uuid4(),
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                metadata=metadata,
                occurred_at=self._clock.now(),
            )
        )
