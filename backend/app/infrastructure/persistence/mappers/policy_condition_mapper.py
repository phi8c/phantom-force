from app.domain.entities.policy_condition import (
    PolicyCondition,
)

from app.domain.enums.policy_operator import (
    PolicyOperator,
)

from app.infrastructure.persistence.models.policy_condition_model import (
    PolicyConditionModel,
)


class PolicyConditionMapper:

    @staticmethod
    def to_domain(
        model: PolicyConditionModel,
    ) -> PolicyCondition:

        return PolicyCondition(
            id=model.id,
            policy_id=model.policy_id,
            attribute_path=model.attribute_path,
            operator=PolicyOperator(model.operator),
            value=model.value,
        )

    @staticmethod
    def to_model(
        entity: PolicyCondition,
    ) -> PolicyConditionModel:

        return PolicyConditionModel(
            id=entity.id,
            policy_id=entity.policy_id,
            attribute_path=entity.attribute_path,
            operator=entity.operator.value,
            value=entity.value,
        )