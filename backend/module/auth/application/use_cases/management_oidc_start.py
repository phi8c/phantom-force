from module.auth.application.dto.response.start_oidc_response import StartOidcResult
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.oidc_authentication_service import (
    OidcAuthenticationService,
)
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.exception.exceptions import AuthenticationMethodNotAllowedError


class ManagementOidcStartUseCase:
    def __init__(self, policies: AuthPolicyResolver, oidc: OidcAuthenticationService):
        self._policies = policies
        self._oidc = oidc

    async def execute(self) -> StartOidcResult:
        policy = await self._policies.resolve_management()
        if policy.auth_method is not AuthProvider.ENTRA:
            raise AuthenticationMethodNotAllowedError(
                "Management authentication policy does not allow Microsoft Entra"
            )
        return await self._oidc.start(policy)
