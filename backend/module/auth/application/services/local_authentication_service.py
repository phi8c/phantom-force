from uuid import uuid4

from module.auth.application.dto.response.local_login_response import LocalLoginResult
from module.auth.application.dto.response.resolved_auth_policy import ResolvedAuthPolicy
from module.auth.application.services.security_audit_service import SecurityAuditService
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
from module.auth.domain.contracts.lockout_policy import LockoutPolicy
from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.password_hasher import PasswordHasher
from module.auth.domain.contracts.token_service import TokenService
from module.auth.domain.contracts.unit_of_work import UnitOfWork
from module.auth.domain.entities.auth_session import AuthSession
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.exception.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
)
from module.auth.domain.services.mfa_policy import MfaPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.value_objects.mfa_challenge import MfaChallenge
from module.user.facade.contract import UserModuleFacade


class LocalAuthenticationService:
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
        mfa_policy: MfaPolicy,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._users = user_facade
        self._credentials = credential_repository
        self._sessions = auth_session_repository
        self._mfa_challenges = mfa_challenge_store
        self._hasher = password_hasher
        self._tokens = token_service
        self._lockout = lockout_policy
        self._session_expiry = session_expiry_policy
        self._mfa = mfa_policy
        self._audit = security_audit

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
        device_fingerprint: str | None,
        policy: ResolvedAuthPolicy,
    ) -> LocalLoginResult:
        user = await self._users.get_user_by_email(email)
        if user is None or user.status != "active" or not user.email_verified:
            raise InvalidCredentialsError()

        credential = await self._credentials.get_by_user_id(user.id)
        if credential is None:
            raise InvalidCredentialsError()

        now = self._clock.now()
        if self._lockout.is_locked(credential.locked_until, now):
            raise AccountLockedError(credential.locked_until)

        if not self._hasher.verify(password, credential.password_hash):
            async with self._uow:
                credential.failed_attempts += 1
                lock_duration = self._lockout.next_lock_duration(
                    credential.failed_attempts
                )
                if lock_duration is not None:
                    credential.locked_until = now + lock_duration
                await self._credentials.update(credential)
                if self._audit is not None:
                    await self._audit.record(
                        "auth.login.failed",
                        actor_user_id=user.id,
                        target_type="user",
                        target_id=user.id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_fingerprint=device_fingerprint,
                        metadata={"method": "local", "locked": lock_duration is not None},
                    )
                await self._uow.commit()
            raise InvalidCredentialsError()

        async with self._uow:
            credential.failed_attempts = 0
            credential.locked_until = None
            await self._credentials.update(credential)

            if self._mfa.enrollment_is_required(
                policy.require_mfa,
                credential.mfa_enabled,
            ):
                await self._uow.commit()
                return LocalLoginResult(status="mfa_enrollment_required")

            if self._mfa.is_required(policy.require_mfa, credential.mfa_enabled):
                challenge = MfaChallenge(
                    user_id=user.id,
                    auth_method=AuthProvider.LOCAL,
                    context_type=policy.context_type,
                    knowledge_space_id=policy.knowledge_space_id,
                    idle_timeout_minutes=policy.idle_timeout_minutes,
                    absolute_timeout_minutes=policy.absolute_timeout_minutes,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    created_at=now,
                    expires_at=self._mfa.challenge_expires_at(now),
                )
                challenge_id = await self._mfa_challenges.create_challenge(challenge)
                if self._audit is not None:
                    await self._audit.record(
                        "auth.mfa.challenge.created",
                        actor_user_id=user.id,
                        target_type="user",
                        target_id=user.id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_fingerprint=device_fingerprint,
                        metadata={"method": "local"},
                    )
                await self._uow.commit()
                return LocalLoginResult(
                    status="mfa_required",
                    mfa_challenge_id=challenge_id,
                )

            raw_token = self._tokens.generate_raw_token()
            session = AuthSession.create(
                id=uuid4(),
                user_id=user.id,
                session_token_hash=self._tokens.hash(raw_token),
                auth_method=AuthProvider.LOCAL,
                context_type=policy.context_type,
                knowledge_space_id=policy.knowledge_space_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                now=now,
                idle_expires_at=self._session_expiry.compute_idle_expiry(
                    now,
                    policy.idle_timeout_minutes,
                ),
                absolute_expires_at=self._session_expiry.compute_absolute_expiry(
                    now,
                    policy.absolute_timeout_minutes,
                ),
            )
            await self._sessions.add(session)
            if self._audit is not None:
                await self._audit.record(
                    "auth.session.created",
                    actor_user_id=user.id,
                    target_type="auth_session",
                    target_id=session.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    metadata={
                        "method": "local",
                        "context": policy.context_type.value,
                    },
                )
            await self._uow.commit()

        return LocalLoginResult(status="success", session_token=raw_token)
