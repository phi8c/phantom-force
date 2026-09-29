from __future__ import annotations


class WeakPasswordError(
    Exception,
):
    pass


class InvalidCredentialsError(
    Exception,
):
    pass


class AccountLockedError(
    Exception,
):

    def __init__(
        self,
        locked_until,
    ):
        self.locked_until = locked_until
        super().__init__(
            "Account is temporarily locked",
        )


class AccountDisabledError(
    Exception,
):
    pass


class MfaRequiredError(
    Exception,
):
    pass


class MfaEnrollmentRequiredError(
    Exception,
):
    pass


class InvalidMfaChallengeError(Exception):
    pass


class SessionInvalidError(
    Exception,
):
    pass


class SessionExpiredError(
    Exception,
):
    pass


class AuthenticationPolicyMissingError(Exception):
    pass


class AuthenticationPolicyInactiveError(Exception):
    pass


class AuthenticationMethodNotAllowedError(Exception):
    pass


class InvalidAuthenticationContextError(Exception):
    pass


class KnowledgeSpaceContextMismatchError(Exception):
    pass


class KnowledgeSpaceNotFoundError(Exception):
    pass


class InvalidVerificationTokenError(Exception):
    pass


class ExpiredVerificationTokenError(Exception):
    pass


class VerificationDeliveryError(Exception):
    pass


class OidcStateInvalidError(Exception):
    pass


class OidcTransactionExpiredError(Exception):
    pass


class OidcTokenValidationError(Exception):
    pass


class OidcTenantMismatchError(Exception):
    pass


class ExternalIdentityConflictError(Exception):
    pass


class ExplicitAccountLinkRequiredError(Exception):
    pass
