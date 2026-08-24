from module.enterprise.domain.entities.enterprise import (
    Enterprise,
)

from module.enterprise.infrastructure.persistence.models.enterprise_model import (
    EnterpriseModel,
)


class EnterpriseMapper:

    @staticmethod
    def to_entity(
        model: EnterpriseModel,
    ) -> Enterprise:

        return Enterprise(
            id=model.id,

            code=model.code,

            name=model.name,

            description=model.description,

            status=model.status,

            created_at=model.created_at,

            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Enterprise,
    ) -> EnterpriseModel:

        return EnterpriseModel(
            id=entity.id,

            code=entity.code,

            name=entity.name,

            description=entity.description,

            status=entity.status,

            created_at=entity.created_at,

            updated_at=entity.updated_at,
        )