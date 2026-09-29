import base64
from datetime import timedelta
import hashlib
import secrets

from module.auth.application.dto.response.resolved_auth_policy import ResolvedAuthPolicy
from module.auth.application.dto.response.start_oidc_response import StartOidcResult
from module.auth.application.dto.response.verified_oidc_authentication import (
    VerifiedOidcAuthentication,
)
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.oidc_provider import OidcProvider
from module.auth.domain.contracts.oidc_transaction_store import OidcTransactionStore
from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)


OIDC_TRANSACTION_TTL = timedelta(minutes=10)


class OidcAuthenticationService:
    def __init__(
        self,
        clock: Clock,
        provider: OidcProvider,
        transaction_store: OidcTransactionStore,
    ):
        self._clock = clock
        self._provider = provider
        self._transactions = transaction_store

    async def start(self, policy: ResolvedAuthPolicy) -> StartOidcResult:
        if not policy.tenant_id:
            raise ValueError("Microsoft Entra policy requires a tenant")
        now = self._clock.now()
        nonce = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        state = await self._transactions.create_transaction(
            OidcAuthorizationTransaction(
                context_type=policy.context_type,
                knowledge_space_id=policy.knowledge_space_id,
                expected_tenant_id=policy.tenant_id,
                nonce=nonce,
                code_verifier=code_verifier,
                require_mfa=policy.require_mfa,
                idle_timeout_minutes=policy.idle_timeout_minutes,
                absolute_timeout_minutes=policy.absolute_timeout_minutes,
                created_at=now,
                expires_at=now + OIDC_TRANSACTION_TTL,
            )
        )
        return StartOidcResult(
            authorization_url=self._provider.build_authorization_url(
                expected_tenant_id=policy.tenant_id,
                state=state,
                nonce=nonce,
                code_challenge=code_challenge,
            )
        )

    async def complete(
        self,
        state: str,
        code: str,
    ) -> VerifiedOidcAuthentication:
        transaction = await self._transactions.take_transaction(
            state,
            self._clock.now(),
        )
        user_info = await self._provider.exchange_code_and_verify(
            expected_tenant_id=transaction.expected_tenant_id,
            code=code,
            code_verifier=transaction.code_verifier,
            expected_nonce=transaction.nonce,
        )
        return VerifiedOidcAuthentication(
            transaction=transaction,
            user_info=user_info,
        )

    async def cancel(self, state: str) -> None:
        await self._transactions.take_transaction(
            state,
            self._clock.now(),
        )
