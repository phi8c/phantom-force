from __future__ import annotations

from uuid import uuid4

from module.auth.domain.contracts.unit_of_work import (
    UnitOfWork,
)

from module.auth.domain.contracts.clock import (
    Clock,
)
from module.auth.domain.contracts.credential_repository import (
    CredentialRepository,
)
from module.auth.domain.contracts.password_hasher import (
    PasswordHasher,
)
from module.auth.domain.contracts.token_service import (
    TokenService,
)
from module.auth.domain.contracts.verification_token_repository import (
    VerificationTokenRepository,
)
from module.auth.domain.contracts.verification_email_sender import (
    VerificationEmailSender,
)
from module.auth.domain.entities.credential import (
    Credential,
)
from module.auth.domain.entities.verification_token import (
    VerificationToken,
)
from module.auth.domain.enums.token_purpose import (
    TokenPurpose,
)
from module.auth.domain.exception.exceptions import (
    WeakPasswordError,
)
from module.auth.domain.services.password_policy import (
    PasswordPolicy,
)
from module.auth.domain.services.verification_token_policy import (
    VerificationTokenPolicy,
)

from module.user.facade.contract import (
    UserModuleFacade,
)
from module.user.facade.exceptions import UserAlreadyExistsError
from module.auth.application.dto.request.register_local_user_request import (
    RegisterLocalUserRequest,
)
from module.auth.application.dto.response.register_local_user_response import (
    RegisterLocalUserResult,
)
from module.auth.application.services.security_audit_service import SecurityAuditService


class RegisterLocalUserUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        user_facade: UserModuleFacade,
        credential_repository: CredentialRepository,
        verification_token_repository: VerificationTokenRepository,
        password_hasher: PasswordHasher,
        password_policy: PasswordPolicy,
        verification_token_policy: VerificationTokenPolicy,
        token_service: TokenService,
        verification_email_sender: VerificationEmailSender,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._user_facade = user_facade
        self._credentials = credential_repository
        self._verification_tokens = verification_token_repository
        self._hasher = password_hasher
        self._password_policy = password_policy
        self._verification_token_policy = verification_token_policy
        self._token_service = token_service
        self._verification_email_sender = verification_email_sender
        self._audit = security_audit

    async def execute(
        self,
        request: RegisterLocalUserRequest,
    ) -> RegisterLocalUserResult:

        if not self._password_policy.is_valid_length(
            request.password,
        ):
            raise WeakPasswordError(
                "Password phai co it nhat 12 ky tu",
            )

        generic_result = RegisterLocalUserResult(
            message="Neu email hop le, ban se nhan duoc email xac thuc.",
        )

        existing = await self._user_facade.get_user_by_email(
            request.email,
        )

        if existing is not None:
            # Chong user enumeration: khong tao trung, tra ve y het
            # truong hop email moi va thanh cong.
            return generic_result

        async with self._uow:

            try:
                user_dto = await self._user_facade.create_user(
                    request.email,
                )
            except UserAlreadyExistsError:
                await self._uow.rollback()
                return generic_result

            now = self._clock.now()

            credential = Credential.create(
                user_id=user_dto.id,
                password_hash=self._hasher.hash(
                    request.password,
                ),
                password_algo=self._hasher.algorithm_name,
                now=now,
            )

            await self._credentials.add(
                credential,
            )

            raw_token = self._token_service.generate_raw_token()

            verification_token = VerificationToken.create_for_purpose(
                id=uuid4(),
                user_id=user_dto.id,
                token_hash=self._token_service.hash(
                    raw_token,
                ),
                purpose=TokenPurpose.EMAIL_VERIFY,
                now=now,
                ttl=self._verification_token_policy.ttl_for(
                    TokenPurpose.EMAIL_VERIFY,
                ),
            )

            await self._verification_tokens.add(
                verification_token,
            )

            await self._verification_email_sender.send_verification_email(
                recipient=user_dto.email,
                raw_token=raw_token,
            )
            if self._audit is not None:
                await self._audit.record(
                    "auth.registration.created",
                    actor_user_id=user_dto.id,
                    target_type="user",
                    target_id=user_dto.id,
                )

            await self._uow.commit()

        return generic_result
