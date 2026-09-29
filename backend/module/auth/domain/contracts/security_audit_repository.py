from abc import ABC, abstractmethod

from module.auth.domain.entities.security_audit_event import SecurityAuditEvent


class SecurityAuditRepository(ABC):
    @abstractmethod
    async def add(self, event: SecurityAuditEvent) -> None:
        pass
