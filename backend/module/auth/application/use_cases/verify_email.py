from module.auth.application.dto.request.verify_email_request import VerifyEmailRequest
from module.auth.application.dto.response.verify_email_response import VerifyEmailResult
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.token_service import TokenService
from module.auth.domain.contracts.unit_of_work import UnitOfWork
from module.auth.domain.contracts.verification_token_repository import (
    VerificationTokenRepository,
)
from module.auth.domain.enums.token_purpose import TokenPurpose
from module.auth.domain.exception.exceptions import (
    ExpiredVerificationTokenError,
    InvalidVerificationTokenError,
)
from module.user.facade.contract import UserModuleFacade
from module.auth.application.services.security_audit_service import SecurityAuditService


class VerifyEmailUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        user_facade: UserModuleFacade,
        verification_token_repository: VerificationTokenRepository,
        token_service: TokenService,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._users = user_facade
        self._verification_tokens = verification_token_repository
        self._token_service = token_service
        self._audit = security_audit

    async def execute(self, request: VerifyEmailRequest) -> VerifyEmailResult:
        token_hash = self._token_service.hash(request.raw_token)

        async with self._uow:
            token = await self._verification_tokens.get_by_token_hash_for_update(
                token_hash
            )
            if (
                token is None
                or token.purpose is not TokenPurpose.EMAIL_VERIFY
                or token.is_used()
            ):
                raise InvalidVerificationTokenError(
                    "Verification token is invalid or has already been used"
                )

            now = self._clock.now()
            if token.is_expired(now):
                raise ExpiredVerificationTokenError(
                    "Verification token has expired"
                )

            token.consume(now)
            await self._users.mark_email_verified(token.user_id, verified_at=now)
            await self._verification_tokens.update(token)
            if self._audit is not None:
                await self._audit.record(
                    "auth.email.verified",
                    actor_user_id=token.user_id,
                    target_type="user",
                    target_id=token.user_id,
                )
            await self._uow.commit()

        return VerifyEmailResult(message="Email verified successfully")
