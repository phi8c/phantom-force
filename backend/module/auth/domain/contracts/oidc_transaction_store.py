from abc import ABC, abstractmethod
from datetime import datetime

from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)


class OidcTransactionStore(ABC):
    @abstractmethod
    async def create_transaction(
        self,
        transaction: OidcAuthorizationTransaction,
    ) -> str:
        pass

    @abstractmethod
    async def take_transaction(
        self,
        state: str,
        now: datetime,
    ) -> OidcAuthorizationTransaction:
        pass
