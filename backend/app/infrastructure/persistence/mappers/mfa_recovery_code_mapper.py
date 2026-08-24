from app.domain.entities.mfa_recovery_code import (
    MfaRecoveryCode,
)

from app.infrastructure.persistence.models.mfa_recovery_code_model import (
    MfaRecoveryCodeModel,
)


class MfaRecoveryCodeMapper:

    @staticmethod
    def to_domain(
        model: MfaRecoveryCodeModel,
    ) -> MfaRecoveryCode:

        return MfaRecoveryCode(
            id=model.id,
            user_id=model.user_id,
            code_hash=model.code_hash,
            used_at=model.used_at,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: MfaRecoveryCode,
    ) -> MfaRecoveryCodeModel:

        return MfaRecoveryCodeModel(
            id=entity.id,
            user_id=entity.user_id,
            code_hash=entity.code_hash,
            used_at=entity.used_at,
            created_at=entity.created_at,
        )