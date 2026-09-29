from uuid import uuid4

from module.auth.application.dto.request.verify_mfa_request import VerifyMfaRequest
from module.auth.application.dto.response.local_login_response import LocalLoginResult
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
from module.auth.domain.contracts.encryptor import Encryptor
from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.mfa_provider import MfaProvider
from module.auth.domain.contracts.token_service import TokenService
from module.auth.domain.contracts.unit_of_work import UnitOfWork
from module.auth.domain.entities.auth_session import AuthSession
from module.auth.domain.exception.exceptions import InvalidMfaChallengeError
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.user.facade.contract import UserModuleFacade
from module.auth.application.services.security_audit_service import SecurityAuditService


class VerifyMfaUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        user_facade: UserModuleFacade,
        credential_repository: CredentialRepository,
        auth_session_repository: AuthSessionRepository,
        challenge_store: MfaChallengeStore,
        mfa_provider: MfaProvider,
        encryptor: Encryptor,
        token_service: TokenService,
        session_expiry_policy: SessionExpiryPolicy,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._users = user_facade
        self._credentials = credential_repository
        self._sessions = auth_session_repository
        self._challenges = challenge_store
        self._mfa = mfa_provider
        self._encryptor = encryptor
        self._tokens = token_service
        self._session_expiry = session_expiry_policy
        self._audit = security_audit

    async def execute(self, request: VerifyMfaRequest) -> LocalLoginResult:
        now = self._clock.now()
        challenge = await self._challenges.take_challenge(
            request.challenge_id,
            now,
        )
        if challenge is None:
            raise InvalidMfaChallengeError("MFA challenge is invalid or expired")

        user = await self._users.get_user(challenge.user_id)
        credential = await self._credentials.get_by_user_id(challenge.user_id)
        if (
            user is None
            or user.status != "active"
            or not user.email_verified
            or credential is None
            or not credential.mfa_enabled
            or credential.mfa_secret_encrypted is None
        ):
            raise InvalidMfaChallengeError("MFA challenge is invalid or expired")

        secret = await self._encryptor.decrypt(credential.mfa_secret_encrypted)
        if not self._mfa.verify_totp(secret, request.code):
            raise InvalidMfaChallengeError("MFA challenge is invalid or expired")

        raw_token = self._tokens.generate_raw_token()
        session = AuthSession.create(
            id=uuid4(),
            user_id=user.id,
            session_token_hash=self._tokens.hash(raw_token),
            auth_method=challenge.auth_method,
            context_type=challenge.context_type,
            knowledge_space_id=challenge.knowledge_space_id,
            ip_address=challenge.ip_address,
            user_agent=challenge.user_agent,
            device_fingerprint=challenge.device_fingerprint,
            now=now,
            idle_expires_at=self._session_expiry.compute_idle_expiry(
                now,
                challenge.idle_timeout_minutes,
            ),
            absolute_expires_at=self._session_expiry.compute_absolute_expiry(
                now,
                challenge.absolute_timeout_minutes,
            ),
            identity_link_id=challenge.identity_link_id,
            mfa_verified_at=now,
        )

        async with self._uow:
            await self._sessions.add(session)
            if self._audit is not None:
                await self._audit.record(
                    "auth.mfa.verified",
                    actor_user_id=user.id,
                    target_type="auth_session",
                    target_id=session.id,
                    ip_address=challenge.ip_address,
                    user_agent=challenge.user_agent,
                    device_fingerprint=challenge.device_fingerprint,
                    metadata={"method": challenge.auth_method.value},
                )
            await self._uow.commit()

        return LocalLoginResult(status="success", session_token=raw_token)
