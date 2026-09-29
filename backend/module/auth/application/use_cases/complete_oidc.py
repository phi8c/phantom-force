from module.auth.application.dto.request.complete_oidc_request import CompleteOidcRequest
from module.auth.application.services.oidc_authentication_service import (
    OidcAuthenticationService,
)
from module.auth.application.services.entra_authentication_service import (
    EntraAuthenticationService,
)
from module.auth.application.dto.response.local_login_response import LocalLoginResult


class CompleteOidcUseCase:
    def __init__(
        self,
        oidc: OidcAuthenticationService,
        entra_authentication: EntraAuthenticationService,
    ):
        self._oidc = oidc
        self._entra_authentication = entra_authentication

    async def execute(
        self,
        request: CompleteOidcRequest,
    ) -> LocalLoginResult:
        verified = await self._oidc.complete(state=request.state, code=request.code)
        return await self._entra_authentication.authenticate(
            verified,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            device_fingerprint=request.device_fingerprint,
        )

    async def cancel(self, state: str) -> None:
        await self._oidc.cancel(state)
