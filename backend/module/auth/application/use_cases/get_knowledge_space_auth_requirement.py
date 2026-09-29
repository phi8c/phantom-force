from uuid import UUID

from module.auth.application.dto.response.knowledge_space_auth_requirement import (
    KnowledgeSpaceAuthRequirement,
)
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver


class GetKnowledgeSpaceAuthRequirementUseCase:
    def __init__(self, policy_resolver: AuthPolicyResolver):
        self._policy_resolver = policy_resolver

    async def execute(self, knowledge_space_id: UUID) -> KnowledgeSpaceAuthRequirement:
        policy = await self._policy_resolver.resolve_knowledge_space(
            knowledge_space_id
        )
        return KnowledgeSpaceAuthRequirement(
            auth_method=policy.auth_method,
            require_mfa=policy.require_mfa,
        )
