from app.domain.entities.role_permission import (
    RolePermission,
)

from app.infrastructure.persistence.models.role_permission_model import (
    RolePermissionModel,
)


class RolePermissionMapper:

    @staticmethod
    def to_domain(
        model: RolePermissionModel,
    ) -> RolePermission:

        return RolePermission(
            role_id=model.role_id,
            permission_id=model.permission_id,
        )

    @staticmethod
    def to_model(
        entity: RolePermission,
    ) -> RolePermissionModel:

        return RolePermissionModel(
            role_id=entity.role_id,
            permission_id=entity.permission_id,
        )