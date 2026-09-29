from dataclasses import dataclass

from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.oidc_transaction_store import OidcTransactionStore
from module.auth.infrastructure.mfa.in_memory_challenge_store import (
    InMemoryMfaChallengeStore,
)
from module.auth.infrastructure.oidc.in_memory_transaction_store import (
    InMemoryOidcTransactionStore,
)


@dataclass(frozen=True)
class AuthRuntime:
    mfa_challenge_store: MfaChallengeStore
    oidc_transaction_store: OidcTransactionStore


def create_auth_runtime() -> AuthRuntime:
    return AuthRuntime(
        mfa_challenge_store=InMemoryMfaChallengeStore(),
        oidc_transaction_store=InMemoryOidcTransactionStore(),
    )
