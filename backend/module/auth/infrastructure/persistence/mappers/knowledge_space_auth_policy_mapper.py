from module.auth.domain.entities.knowledge_space_auth_policy import (
    KnowledgeSpaceAuthPolicy,
)
from module.auth.infrastructure.persistence.mappers.policy_auth_method import (
    auth_method_to_database,
    auth_method_to_domain,
)
from module.auth.infrastructure.persistence.models.knowledge_space_auth_policy_model import (
    KnowledgeSpaceAuthPolicyModel,
)


class KnowledgeSpaceAuthPolicyMapper:
    @staticmethod
    def to_domain(model: KnowledgeSpaceAuthPolicyModel) -> KnowledgeSpaceAuthPolicy:
        return KnowledgeSpaceAuthPolicy(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            auth_method=auth_method_to_domain(model.auth_method),
            tenant_id=model.tenant_id,
            require_mfa=model.require_mfa,
            idle_timeout_minutes=model.idle_timeout_minutes,
            absolute_timeout_minutes=model.absolute_timeout_minutes,
            is_active=model.is_active,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(policy: KnowledgeSpaceAuthPolicy) -> KnowledgeSpaceAuthPolicyModel:
        return KnowledgeSpaceAuthPolicyModel(
            id=policy.id,
            knowledge_space_id=policy.knowledge_space_id,
            auth_method=auth_method_to_database(policy.auth_method),
            tenant_id=policy.tenant_id,
            require_mfa=policy.require_mfa,
            idle_timeout_minutes=policy.idle_timeout_minutes,
            absolute_timeout_minutes=policy.absolute_timeout_minutes,
            is_active=policy.is_active,
            created_by=policy.created_by,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )

    @staticmethod
    def merge_into_model(
        model: KnowledgeSpaceAuthPolicyModel,
        policy: KnowledgeSpaceAuthPolicy,
    ) -> None:
        model.auth_method = auth_method_to_database(policy.auth_method)
        model.tenant_id = policy.tenant_id
        model.require_mfa = policy.require_mfa
        model.idle_timeout_minutes = policy.idle_timeout_minutes
        model.absolute_timeout_minutes = policy.absolute_timeout_minutes
        model.is_active = policy.is_active
        model.created_by = policy.created_by
