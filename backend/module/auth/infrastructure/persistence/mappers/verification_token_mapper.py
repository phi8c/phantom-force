from module.auth.domain.entities.verification_token import (
    VerificationToken,
)

from module.auth.domain.enums.token_purpose import (
    TokenPurpose,
)

from module.auth.infrastructure.persistence.models.verification_token_model import (
    VerificationTokenModel,
)


class VerificationTokenMapper:

    @staticmethod
    def to_domain(
        model: VerificationTokenModel,
    ) -> VerificationToken:

        return VerificationToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            purpose=TokenPurpose(model.purpose),
            expires_at=model.expires_at,
            used_at=model.used_at,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: VerificationToken,
    ) -> VerificationTokenModel:

        return VerificationTokenModel(
            id=entity.id,
            user_id=entity.user_id,
            token_hash=entity.token_hash,
            purpose=entity.purpose.value,
            expires_at=entity.expires_at,
            used_at=entity.used_at,
            created_at=entity.created_at,
        )
