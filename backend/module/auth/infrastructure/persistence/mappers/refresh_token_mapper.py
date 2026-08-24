from app.domain.entities.refresh_token import (
    RefreshToken,
)

from app.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)


class RefreshTokenMapper:

    @staticmethod
    def to_domain(
        model: RefreshTokenModel,
    ) -> RefreshToken:

        return RefreshToken(
            id=model.id,
            session_id=model.session_id,
            token_hash=model.token_hash,
            issued_at=model.issued_at,
            expires_at=model.expires_at,
            used_at=model.used_at,
            revoked_at=model.revoked_at,
            replaced_by=model.replaced_by,
        )

    @staticmethod
    def to_model(
        entity: RefreshToken,
    ) -> RefreshTokenModel:

        return RefreshTokenModel(
            id=entity.id,
            session_id=entity.session_id,
            token_hash=entity.token_hash,
            issued_at=entity.issued_at,
            expires_at=entity.expires_at,
            used_at=entity.used_at,
            revoked_at=entity.revoked_at,
            replaced_by=entity.replaced_by,
        )