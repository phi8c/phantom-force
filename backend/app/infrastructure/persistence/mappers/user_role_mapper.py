from app.domain.entities.user_role import (
    UserRole,
)

from app.domain.enums.role_assignment_source import (
    RoleAssignmentSource,
)

from app.infrastructure.persistence.models.user_role_model import (
    UserRoleModel,
)


class UserRoleMapper:

    @staticmethod
    def to_domain(
        model: UserRoleModel,
    ) -> UserRole:

        return UserRole(
            user_id=model.user_id,
            role_id=model.role_id,
            source=RoleAssignmentSource(model.source),
            assigned_by=model.assigned_by,
            assigned_at=model.assigned_at,
        )

    @staticmethod
    def to_model(
        entity: UserRole,
    ) -> UserRoleModel:

        return UserRoleModel(
            user_id=entity.user_id,
            role_id=entity.role_id,
            source=entity.source.value,
            assigned_by=entity.assigned_by,
            assigned_at=entity.assigned_at,
        )