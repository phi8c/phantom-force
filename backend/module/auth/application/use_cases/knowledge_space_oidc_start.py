from module.auth.application.dto.request.knowledge_space_oidc_start_request import (
    KnowledgeSpaceOidcStartRequest,
)
from module.auth.application.dto.response.start_oidc_response import StartOidcResult
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.oidc_authentication_service import (
    OidcAuthenticationService,
)
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.exception.exceptions import AuthenticationMethodNotAllowedError


class KnowledgeSpaceOidcStartUseCase:
    def __init__(self, policies: AuthPolicyResolver, oidc: OidcAuthenticationService):
        self._policies = policies
        self._oidc = oidc

    async def execute(
        self,
        request: KnowledgeSpaceOidcStartRequest,
    ) -> StartOidcResult:
        policy = await self._policies.resolve_knowledge_space(
            request.knowledge_space_id
        )
        if policy.auth_method is not AuthProvider.ENTRA:
            raise AuthenticationMethodNotAllowedError(
                "Knowledge Space policy does not allow Microsoft Entra"
            )
        return await self._oidc.start(policy)
