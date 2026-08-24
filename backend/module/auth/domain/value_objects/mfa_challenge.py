from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)

from module.auth.domain.contracts.auth_session_repository import (
    AuthSessionRepository,
)
from module.auth.domain.contracts.clock import (
    Clock,
)
from module.auth.domain.contracts.credential_repository import (
    CredentialRepository,
)
from module.auth.domain.contracts.mfa_challenge_store import (
    MfaChallengeStore,
)
from module.auth.domain.contracts.password_hasher import (
    PasswordHasher,
)
from module.auth.domain.contracts.token_service import (
    TokenService,
)
from module.auth.domain.entities.auth_session import (
    AuthSession,
)
from module.auth.domain.enums.auth_provider import (
    AuthProvider,
)
from module.auth.domain.exception.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
)
from module.auth.domain.services.lockout_policy import (
    LockoutPolicy,
)
from module.auth.domain.services.session_expiry_policy import (
    SessionExpiryPolicy,
)
from module.auth.domain.value_objects.mfa_challenge import (
    MfaChallenge,
)

from module.user.facade.contract import (
    UserModuleFacade,
)


@dataclass
class LocalLoginRequest:

    email: str

    password: str

    ip_address: str | None

    user_agent: str | None

    device_fingerprint: str | None


@dataclass
class LocalLoginResult:

    status: Literal[
        "success",
        "mfa_required",
    ]

    session_token: str | None = None

    mfa_challenge_id: str | None = None


class LocalLoginUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        user_facade: UserModuleFacade,
        credential_repository: CredentialRepository,
        auth_session_repository: AuthSessionRepository,
        mfa_challenge_store: MfaChallengeStore,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        lockout_policy: LockoutPolicy,
        session_expiry_policy: SessionExpiryPolicy,
    ):
        self._uow = uow
        self._clock = clock
        self._user_facade = user_facade
        self._credentials = credential_repository
        self._auth_sessions = auth_session_repository
        self._mfa_challenges = mfa_challenge_store
        self._hasher = password_hasher
        self._token_service = token_service
        self._lockout_policy = lockout_policy
        self._session_expiry_policy = session_expiry_policy

    async def execute(
        self,
        request: LocalLoginRequest,
    ) -> LocalLoginResult:

        user_dto = await self._user_facade.get_user_by_email(
            request.email,
        )

        if user_dto is None:
            # Khong tiet lo email khong ton tai - loi giong het sai password.
            raise InvalidCredentialsError()

        if user_dto.status != "active":
            # Khong tiet lo ly do cu the (disabled/pending) - tranh xac nhan
            # gian tiep trang thai tai khoan cho ke tan cong.
            raise InvalidCredentialsError()

        credential = await self._credentials.get_by_user_id(
            user_dto.id,
        )

        if credential is None:
            # User chi co SSO, chua tung tao local credential.
            raise InvalidCredentialsError()

        now = self._clock.now()

        if self._lockout_policy.is_locked(
            credential.locked_until,
            now,
        ):
            raise AccountLockedError(
                credential.locked_until,
            )

        if not self._hasher.verify(
            request.password,
            credential.password_hash,
        ):

            async with self._uow:

                credential.failed_attempts += 1

                lock_duration = self._lockout_policy.next_lock_duration(
                    credential.failed_attempts,
                )

                if lock_duration is not None:
                    credential.locked_until = now + lock_duration

                await self._credentials.update(
                    credential,
                )

                await self._uow.commit()

            raise InvalidCredentialsError()

        async with self._uow:

            credential.failed_attempts = 0
            credential.locked_until = None

            await self._credentials.update(
                credential,
            )

            if credential.mfa_enabled:

                challenge = MfaChallenge(
                    user_id=user_dto.id,
                    auth_method=AuthProvider.LOCAL,
                    ip_address=request.ip_address,
                    user_agent=request.user_agent,
                    device_fingerprint=request.device_fingerprint,
                    created_at=now,
                )

                challenge_id = await self._mfa_challenges.create_challenge(
                    challenge,
                )

                await self._uow.commit()

                return LocalLoginResult(
                    status="mfa_required",
                    mfa_challenge_id=challenge_id,
                )

            raw_token = self._token_service.generate_raw_token()

            session = AuthSession.create(
                id=uuid4(),
                user_id=user_dto.id,
                session_token_hash=self._token_service.hash(
                    raw_token,
                ),
                auth_method=AuthProvider.LOCAL,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                device_fingerprint=request.device_fingerprint,
                now=now,
                idle_expires_at=self._session_expiry_policy.compute_idle_expiry(
                    now,
                ),
                absolute_expires_at=self._session_expiry_policy.compute_absolute_expiry(
                    now,
                ),
            )

            await self._auth_sessions.add(
                session,
            )

            await self._uow.commit()

        return LocalLoginResult(
            status="success",
            session_token=raw_token,
        )