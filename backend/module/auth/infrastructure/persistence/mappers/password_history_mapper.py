from app.domain.entities.password_history import (
    PasswordHistory,
)

from app.infrastructure.persistence.models.password_history_model import (
    PasswordHistoryModel,
)


class PasswordHistoryMapper:

    @staticmethod
    def to_domain(
        model: PasswordHistoryModel,
    ) -> PasswordHistory:

        return PasswordHistory(
            id=model.id,
            user_id=model.user_id,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: PasswordHistory,
    ) -> PasswordHistoryModel:

        return PasswordHistoryModel(
            id=entity.id,
            user_id=entity.user_id,
            password_hash=entity.password_hash,
            created_at=entity.created_at,
        )