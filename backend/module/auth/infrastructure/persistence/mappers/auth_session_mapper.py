from module.auth.domain.entities.auth_session import (
    AuthSession,
)

from module.auth.domain.enums.auth_provider import (
    AuthProvider,
)
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)

from module.auth.infrastructure.persistence.models.auth_session_model import (
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
            context_type=AuthenticationContextType(model.context_type),
            knowledge_space_id=model.knowledge_space_id,
            identity_link_id=model.identity_link_id,
            authenticated_at=model.authenticated_at,
            mfa_verified_at=model.mfa_verified_at,
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
            context_type=entity.context_type.value,
            knowledge_space_id=entity.knowledge_space_id,
            identity_link_id=entity.identity_link_id,
            authenticated_at=entity.authenticated_at,
            mfa_verified_at=entity.mfa_verified_at,
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
