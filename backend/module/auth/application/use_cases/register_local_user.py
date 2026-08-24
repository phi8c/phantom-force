from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.domain.unit_of_work.unit_of_work import (
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


@dataclass
class RegisterLocalUserRequest:

    email: str

    password: str


@dataclass
class RegisterLocalUserResult:
    """
    1 object duy nhat, ten field ro nghia - thay the cho tuple mo ho.
    raw_verification_token = None khi email da ton tai tu truoc (khong tao
    gi ca, chi tra ket qua giong het truong hop thanh cong).
    """

    message: str

    raw_verification_token: str | None


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
            raw_verification_token=None,
        )

        existing = await self._user_facade.get_user_by_email(
            request.email,
        )

        if existing is not None:
            # Chong user enumeration: khong tao trung, tra ve y het
            # truong hop email moi va thanh cong.
            return generic_result

        async with self._uow:

            user_dto = await self._user_facade.create_user(
                request.email,
            )

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

            await self._uow.commit()

        return RegisterLocalUserResult(
            message=generic_result.message,
            raw_verification_token=raw_token,
        )