from dataclasses import dataclass

from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)
from module.auth.domain.value_objects.oidc_user_info import OidcUserInfo


@dataclass(frozen=True)
class VerifiedOidcAuthentication:
    transaction: OidcAuthorizationTransaction
    user_info: OidcUserInfo
