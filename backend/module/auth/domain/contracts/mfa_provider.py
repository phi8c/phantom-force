from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class MfaProvider(
    ABC,
):

    @abstractmethod
    def generate_secret(
        self,
    ) -> str:
        pass

    @abstractmethod
    def generate_provisioning_uri(
        self,
        secret: str,
        account_email: str,
    ) -> str:
        pass

    @abstractmethod
    def verify_totp(
        self,
        secret: str,
        code: str,
    ) -> bool:
        pass