from uuid import UUID

from module.auth.application.dto.response.resolved_auth_policy import (
    ResolvedAuthPolicy,
)
from module.auth.domain.contracts.knowledge_space_auth_policy_repository import (
    KnowledgeSpaceAuthPolicyRepository,
)
from module.auth.domain.contracts.management_auth_policy_repository import (
    ManagementAuthPolicyRepository,
)
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import (
    AuthenticationPolicyInactiveError,
    AuthenticationPolicyMissingError,
    KnowledgeSpaceNotFoundError,
)
from module.knowledge_space.facade.contract import KnowledgeSpaceModuleFacade


class AuthPolicyResolver:
    def __init__(
        self,
        management_policy_repository: ManagementAuthPolicyRepository,
        knowledge_space_policy_repository: KnowledgeSpaceAuthPolicyRepository,
        knowledge_space_facade: KnowledgeSpaceModuleFacade,
    ):
        self._management_policies = management_policy_repository
        self._knowledge_space_policies = knowledge_space_policy_repository
        self._knowledge_spaces = knowledge_space_facade

    async def resolve_management(self) -> ResolvedAuthPolicy:
        policy = await self._management_policies.get_active()
        if policy is None:
            raise AuthenticationPolicyMissingError(
                "Active management authentication policy is required"
            )
        if not policy.is_active:
            raise AuthenticationPolicyInactiveError(
                "Management authentication policy is inactive"
            )
        return ResolvedAuthPolicy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            auth_method=policy.auth_method,
            tenant_id=policy.tenant_id,
            require_mfa=policy.require_mfa,
            idle_timeout_minutes=policy.idle_timeout_minutes,
            absolute_timeout_minutes=policy.absolute_timeout_minutes,
            reauthentication_minutes=policy.reauthentication_minutes,
        )

    async def resolve_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> ResolvedAuthPolicy:
        knowledge_space = await self._knowledge_spaces.get_knowledge_space(
            knowledge_space_id
        )
        if knowledge_space is None:
            raise KnowledgeSpaceNotFoundError("Knowledge Space not found")

        policy = await self._knowledge_space_policies.get_by_knowledge_space_id(
            knowledge_space_id
        )
        if policy is None:
            raise AuthenticationPolicyMissingError(
                "Knowledge Space authentication policy is required"
            )
        if not policy.is_active:
            raise AuthenticationPolicyInactiveError(
                "Knowledge Space authentication policy is inactive"
            )
        return ResolvedAuthPolicy(
            context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
            knowledge_space_id=knowledge_space_id,
            auth_method=policy.auth_method,
            tenant_id=policy.tenant_id,
            require_mfa=policy.require_mfa,
            idle_timeout_minutes=policy.idle_timeout_minutes,
            absolute_timeout_minutes=policy.absolute_timeout_minutes,
            reauthentication_minutes=None,
        )
