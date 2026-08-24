from app.domain.entities.auth_session import (
    AuthSession,
)

from app.domain.enums.auth_provider import (
    AuthProvider,
)

from app.infrastructure.persistence.models.auth_session_model import (
    AuthSessionModel,
)


class AuthSessionMapper:

    @staticmethod
    def to_domain(
        model: AuthSessionModel,
    ) -> AuthSession:

        return AuthSession(
            id=model.id,
            user_id=model.user_id,
            session_token_hash=model.session_token_hash,
            auth_method=AuthProvider(model.auth_method),
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            device_fingerprint=model.device_fingerprint,
            issued_at=model.issued_at,
            last_seen_at=model.last_seen_at,
            idle_expires_at=model.idle_expires_at,
            absolute_expires_at=model.absolute_expires_at,
            revoked_at=model.revoked_at,
            revoked_reason=model.revoked_reason,
        )

    @staticmethod
    def to_model(
        entity: AuthSession,
    ) -> AuthSessionModel:

        return AuthSessionModel(
            id=entity.id,
            user_id=entity.user_id,
            session_token_hash=entity.session_token_hash,
            auth_method=entity.auth_method.value,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            device_fingerprint=entity.device_fingerprint,
            issued_at=entity.issued_at,
            last_seen_at=entity.last_seen_at,
            idle_expires_at=entity.idle_expires_at,
            absolute_expires_at=entity.absolute_expires_at,
            revoked_at=entity.revoked_at,
            revoked_reason=entity.revoked_reason,
        )