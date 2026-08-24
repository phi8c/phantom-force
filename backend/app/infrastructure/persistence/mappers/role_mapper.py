from app.domain.entities.role import (
    Role,
)

from app.domain.enums.role_source import (
    RoleSource,
)

from app.infrastructure.persistence.models.role_model import (
    RoleModel,
)


class RoleMapper:

    @staticmethod
    def to_domain(
        model: RoleModel,
    ) -> Role:

        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            source=RoleSource(model.source),
            external_role_value=model.external_role_value,
            is_protected=model.is_protected,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Role,
    ) -> RoleModel:

        return RoleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            source=entity.source.value,
            external_role_value=entity.external_role_value,
            is_protected=entity.is_protected,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )