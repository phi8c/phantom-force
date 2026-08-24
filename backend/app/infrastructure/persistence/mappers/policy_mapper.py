from app.domain.entities.policy import (
    Policy,
)

from app.domain.enums.policy_effect import (
    PolicyEffect,
)

from app.infrastructure.persistence.models.policy_model import (
    PolicyModel,
)


class PolicyMapper:

    @staticmethod
    def to_domain(
        model: PolicyModel,
    ) -> Policy:

        return Policy(
            id=model.id,
            name=model.name,
            effect=PolicyEffect(model.effect),
            resource_type=model.resource_type,
            action=model.action,
            priority=model.priority,
            is_active=model.is_active,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Policy,
    ) -> PolicyModel:

        return PolicyModel(
            id=entity.id,
            name=entity.name,
            effect=entity.effect.value,
            resource_type=entity.resource_type,
            action=entity.action,
            priority=entity.priority,
            is_active=entity.is_active,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )