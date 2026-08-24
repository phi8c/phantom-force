from app.domain.entities.user import (
    User,
)

from app.domain.enums.user_status import (
    UserStatus,
)

from app.infrastructure.persistence.models.user_model import (
    UserModel,
)


class UserMapper:

    @staticmethod
    def to_domain(
        model: UserModel,
    ) -> User:

        return User(
            id=model.id,
            email=model.email,
            status=UserStatus(model.status),
            full_name=model.full_name,
            email_verified_at=model.email_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(
        entity: User,
    ) -> UserModel:

        return UserModel(
            id=entity.id,
            email=entity.email,
            status=entity.status.value,
            full_name=entity.full_name,
            email_verified_at=entity.email_verified_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def merge_into_model(
        model: UserModel,
        entity: User,
    ) -> None:

        model.email = entity.email
        model.status = entity.status.value
        model.full_name = entity.full_name
        model.email_verified_at = entity.email_verified_at
        model.deleted_at = entity.deleted_at