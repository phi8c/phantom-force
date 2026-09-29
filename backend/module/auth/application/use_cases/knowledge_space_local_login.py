from module.auth.application.dto.request.knowledge_space_local_login_request import (
    KnowledgeSpaceLocalLoginRequest,
)
from module.auth.application.dto.response.local_login_response import LocalLoginResult
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.local_authentication_service import (
    LocalAuthenticationService,
)
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.exception.exceptions import AuthenticationMethodNotAllowedError


class KnowledgeSpaceLocalLoginUseCase:
    def __init__(
        self,
        policy_resolver: AuthPolicyResolver,
        local_authentication: LocalAuthenticationService,
    ):
        self._policies = policy_resolver
        self._local_authentication = local_authentication

    async def execute(
        self,
        request: KnowledgeSpaceLocalLoginRequest,
    ) -> LocalLoginResult:
        policy = await self._policies.resolve_knowledge_space(
            request.knowledge_space_id
        )
        if policy.auth_method is not AuthProvider.LOCAL:
            raise AuthenticationMethodNotAllowedError(
                "Knowledge Space authentication policy does not allow local login"
            )
        return await self._local_authentication.authenticate(
            email=request.email,
            password=request.password,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            device_fingerprint=request.device_fingerprint,
            policy=policy,
        )
