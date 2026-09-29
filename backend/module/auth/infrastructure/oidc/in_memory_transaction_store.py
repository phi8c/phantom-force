import asyncio
import hashlib
import secrets

from module.auth.domain.contracts.oidc_transaction_store import OidcTransactionStore
from module.auth.domain.exception.exceptions import (
    OidcStateInvalidError,
    OidcTransactionExpiredError,
)
from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)


class InMemoryOidcTransactionStore(OidcTransactionStore):
    def __init__(self):
        self._transactions: dict[str, OidcAuthorizationTransaction] = {}
        self._lock = asyncio.Lock()

    async def create_transaction(
        self,
        transaction: OidcAuthorizationTransaction,
    ) -> str:
        state = secrets.token_urlsafe(32)
        async with self._lock:
            self._transactions = {
                key: value
                for key, value in self._transactions.items()
                if value.expires_at > transaction.created_at
            }
            self._transactions[self._hash(state)] = transaction
        return state

    async def take_transaction(self, state: str, now):
        async with self._lock:
            transaction = self._transactions.pop(self._hash(state), None)
        if transaction is None:
            raise OidcStateInvalidError("OIDC state is invalid or already used")
        if transaction.expires_at <= now:
            raise OidcTransactionExpiredError("OIDC transaction has expired")
        return transaction

    @staticmethod
    def _hash(state: str) -> str:
        return hashlib.sha256(state.encode("utf-8")).hexdigest()
