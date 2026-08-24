from app.domain.entities.audit_log import (
    AuditLog,
)

from app.infrastructure.persistence.models.audit_log_model import (
    AuditLogModel,
)


class AuditLogMapper:

    @staticmethod
    def to_domain(
        model: AuditLogModel,
    ) -> AuditLog:

        return AuditLog(
            id=model.id,
            actor_user_id=model.actor_user_id,
            action=model.action,
            target_type=model.target_type,
            target_id=model.target_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            device_fingerprint=model.device_fingerprint,
            metadata=model.metadata_payload,
            occurred_at=model.occurred_at,
        )

    @staticmethod
    def to_model(
        entity: AuditLog,
    ) -> AuditLogModel:

        return AuditLogModel(
            id=entity.id,
            actor_user_id=entity.actor_user_id,
            action=entity.action,
            target_type=entity.target_type,
            target_id=entity.target_id,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            device_fingerprint=entity.device_fingerprint,
            metadata_payload=entity.metadata,
            occurred_at=entity.occurred_at,
        )