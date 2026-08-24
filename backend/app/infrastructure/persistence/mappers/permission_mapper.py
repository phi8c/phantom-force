from app.domain.entities.permission import (
    Permission,
)

from app.infrastructure.persistence.models.permission_model import (
    PermissionModel,
)


class PermissionMapper:

    @staticmethod
    def to_domain(
        model: PermissionModel,
    ) -> Permission:

        return Permission(
            id=model.id,
            code=model.code,
            resource_type=model.resource_type,
            action=model.action,
            description=model.description,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: Permission,
    ) -> PermissionModel:

        return PermissionModel(
            id=entity.id,
            code=entity.code,
            resource_type=entity.resource_type,
            action=entity.action,
            description=entity.description,
            created_at=entity.created_at,
        )