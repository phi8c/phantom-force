from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from ..value_objects.oidc_user_info import OidcUserInfo


class OidcProvider(
    ABC,
):
    """
    1 impl rieng cho tung provider (EntraOidcProvider, GoogleOidcProvider),
    chon boi factory theo AuthProvider. Domain/application khong biet chi
    tiet endpoint/scope cua tung provider.
    """

    @abstractmethod
    def build_authorization_url(
        self,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        pass

    @abstractmethod
    async def exchange_code_and_verify(
        self,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcUserInfo:
        """
        Doi authorization code lay token tai token_endpoint, verify id_token
        (chu ky/iss/aud/nonce) ngay ben trong impl - tra ve DUY NHAT
        OidcUserInfo, khong tra raw token nao ra ngoai boundary nay.
        """
        pass