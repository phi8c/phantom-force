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


class SessionInvalidError(
    Exception,
):
    pass


class SessionExpiredError(
    Exception,
):
    pass