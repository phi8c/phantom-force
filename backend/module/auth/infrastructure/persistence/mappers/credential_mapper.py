from app.domain.entities.credential import (
    Credential,
)

from app.infrastructure.persistence.models.credential_model import (
    CredentialModel,
)


class CredentialMapper:

    @staticmethod
    def to_domain(
        model: CredentialModel,
    ) -> Credential:

        return Credential(
            user_id=model.user_id,
            password_hash=model.password_hash,
            password_algo=model.password_algo,
            password_changed_at=model.password_changed_at,
            failed_attempts=model.failed_attempts,
            locked_until=model.locked_until,
            mfa_enabled=model.mfa_enabled,
            mfa_secret_encrypted=model.mfa_secret_encrypted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Credential,
    ) -> CredentialModel:

        return CredentialModel(
            user_id=entity.user_id,
            password_hash=entity.password_hash,
            password_algo=entity.password_algo,
            password_changed_at=entity.password_changed_at,
            failed_attempts=entity.failed_attempts,
            locked_until=entity.locked_until,
            mfa_enabled=entity.mfa_enabled,
            mfa_secret_encrypted=entity.mfa_secret_encrypted,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        
    @staticmethod
    def merge_into_model(
        model: CredentialModel,
        entity: Credential,
    ) -> None:

        model.password_hash = entity.password_hash
        model.password_algo = entity.password_algo
        model.password_changed_at = entity.password_changed_at
        model.failed_attempts = entity.failed_attempts
        model.locked_until = entity.locked_until
        model.mfa_enabled = entity.mfa_enabled
        model.mfa_secret_encrypted = entity.mfa_secret_encrypted