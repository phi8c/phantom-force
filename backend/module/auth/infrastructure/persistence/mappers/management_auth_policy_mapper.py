from module.auth.domain.entities.management_auth_policy import ManagementAuthPolicy
from module.auth.infrastructure.persistence.mappers.policy_auth_method import (
    auth_method_to_database,
    auth_method_to_domain,
)
from module.auth.infrastructure.persistence.models.management_auth_policy_model import (
    ManagementAuthPolicyModel,
)


class ManagementAuthPolicyMapper:
    @staticmethod
    def to_domain(model: ManagementAuthPolicyModel) -> ManagementAuthPolicy:
        return ManagementAuthPolicy(
            id=model.id,
            auth_method=auth_method_to_domain(model.auth_method),
            tenant_id=model.tenant_id,
            require_mfa=model.require_mfa,
            idle_timeout_minutes=model.idle_timeout_minutes,
            absolute_timeout_minutes=model.absolute_timeout_minutes,
            reauthentication_minutes=model.reauthentication_minutes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(policy: ManagementAuthPolicy) -> ManagementAuthPolicyModel:
        return ManagementAuthPolicyModel(
            id=policy.id,
            auth_method=auth_method_to_database(policy.auth_method),
            tenant_id=policy.tenant_id,
            require_mfa=policy.require_mfa,
            idle_timeout_minutes=policy.idle_timeout_minutes,
            absolute_timeout_minutes=policy.absolute_timeout_minutes,
            reauthentication_minutes=policy.reauthentication_minutes,
            is_active=policy.is_active,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )

    @staticmethod
    def merge_into_model(
        model: ManagementAuthPolicyModel,
        policy: ManagementAuthPolicy,
    ) -> None:
        model.auth_method = auth_method_to_database(policy.auth_method)
        model.tenant_id = policy.tenant_id
        model.require_mfa = policy.require_mfa
        model.idle_timeout_minutes = policy.idle_timeout_minutes
        model.absolute_timeout_minutes = policy.absolute_timeout_minutes
        model.reauthentication_minutes = policy.reauthentication_minutes
        model.is_active = policy.is_active
