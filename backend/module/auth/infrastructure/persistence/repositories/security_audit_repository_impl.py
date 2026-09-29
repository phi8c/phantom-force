from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.security_audit_repository import (
    SecurityAuditRepository,
)
from module.auth.domain.entities.security_audit_event import SecurityAuditEvent
from module.auth.infrastructure.persistence.models.security_audit_event_model import (
    SecurityAuditEventModel,
)


class SecurityAuditRepositoryImpl(SecurityAuditRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, event: SecurityAuditEvent) -> None:
        self._session.add(
            SecurityAuditEventModel(
                id=event.id,
                actor_user_id=event.actor_user_id,
                action=event.action,
                target_type=event.target_type,
                target_id=event.target_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                device_fingerprint=event.device_fingerprint,
                metadata_payload=event.metadata,
                occurred_at=event.occurred_at,
            )
        )
        await self._session.flush()
