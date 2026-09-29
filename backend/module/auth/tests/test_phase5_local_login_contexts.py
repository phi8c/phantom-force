from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from uuid import uuid4

from module.auth.application.dto.response.resolved_auth_policy import ResolvedAuthPolicy
from module.auth.application.services.local_authentication_service import (
    LocalAuthenticationService,
)
from module.auth.domain.entities.credential import Credential
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.contracts.lockout_policy import LockoutPolicy
from module.auth.domain.exception.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
)
from module.auth.domain.services.mfa_policy import MfaPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.user.facade.dto import UserDTO


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUnitOfWork:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass


class FakeClock:
    def now(self):
        return NOW


class FakeUserFacade:
    def __init__(self):
        self.user = UserDTO(
            id=uuid4(),
            email="user@example.com",
            status="active",
            full_name=None,
            email_verified=True,
        )

    async def get_user_by_email(self, email):
        return self.user


class FakeCredentialRepository:
    def __init__(self, mfa_enabled=False):
        self.credential = Credential(
            user_id=uuid4(),
            password_hash="correct-password",
            password_algo="test",
            password_changed_at=NOW,
            failed_attempts=0,
            locked_until=None,
            mfa_enabled=mfa_enabled,
            mfa_secret_encrypted="secret" if mfa_enabled else None,
            created_at=NOW,
            updated_at=NOW,
        )

    async def get_by_user_id(self, user_id):
        return self.credential

    async def update(self, credential):
        self.credential = credential


class FakePasswordHasher:
    def verify(self, password, password_hash):
        return password == password_hash


class FakeTokenService:
    raw_token = "session-token"

    def generate_raw_token(self):
        return self.raw_token

    def hash(self, raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()


class RecordingSessionRepository:
    def __init__(self):
        self.added = None

    async def add(self, session):
        self.added = session
        return session


class RecordingMfaChallengeStore:
    def __init__(self):
        self.challenge = None

    async def create_challenge(self, challenge):
        self.challenge = challenge
        return "challenge-id"


class LocalLoginContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_management_session_uses_management_context_and_policy_timeouts(self):
        sessions = RecordingSessionRepository()
        service = self._service(sessions=sessions)
        policy = self._policy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
        )

        result = await self._authenticate(service, policy)

        self.assertEqual(result.status, "success")
        self.assertEqual(
            sessions.added.context_type,
            AuthenticationContextType.MANAGEMENT,
        )
        self.assertIsNone(sessions.added.knowledge_space_id)
        self.assertEqual(sessions.added.idle_expires_at, NOW + timedelta(minutes=15))
        self.assertEqual(
            sessions.added.absolute_expires_at,
            NOW + timedelta(minutes=480),
        )

    async def test_knowledge_space_session_is_bound_to_selected_space(self):
        knowledge_space_id = uuid4()
        sessions = RecordingSessionRepository()
        service = self._service(sessions=sessions)
        policy = self._policy(
            context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
            knowledge_space_id=knowledge_space_id,
            idle_timeout_minutes=30,
            absolute_timeout_minutes=240,
        )

        await self._authenticate(service, policy)

        self.assertEqual(sessions.added.knowledge_space_id, knowledge_space_id)
        self.assertEqual(
            sessions.added.context_type,
            AuthenticationContextType.KNOWLEDGE_SPACE,
        )

    async def test_required_mfa_without_enrollment_does_not_create_session(self):
        sessions = RecordingSessionRepository()
        service = self._service(sessions=sessions, mfa_enabled=False)
        policy = self._policy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
            require_mfa=True,
        )

        result = await self._authenticate(service, policy)

        self.assertEqual(result.status, "mfa_enrollment_required")
        self.assertIsNone(sessions.added)

    async def test_wrong_password_records_failed_attempt(self):
        service = self._service(sessions=RecordingSessionRepository())
        policy = self._policy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
        )

        with self.assertRaises(InvalidCredentialsError):
            await service.authenticate(
                email="user@example.com",
                password="wrong-password",
                ip_address=None,
                user_agent=None,
                device_fingerprint=None,
                policy=policy,
            )
        self.assertEqual(service._credentials.credential.failed_attempts, 1)

    async def test_locked_account_is_rejected_before_password_check(self):
        service = self._service(sessions=RecordingSessionRepository())
        service._credentials.credential.locked_until = NOW + timedelta(minutes=5)
        policy = self._policy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
        )

        with self.assertRaises(AccountLockedError):
            await self._authenticate(service, policy)

    async def test_inactive_user_is_rejected(self):
        service = self._service(sessions=RecordingSessionRepository())
        user = service._users.user
        service._users.user = UserDTO(
            id=user.id,
            email=user.email,
            status="disabled",
            full_name=None,
            email_verified=True,
        )
        policy = self._policy(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
        )

        with self.assertRaises(InvalidCredentialsError):
            await self._authenticate(service, policy)

    @staticmethod
    async def _authenticate(service, policy):
        return await service.authenticate(
            email="user@example.com",
            password="correct-password",
            ip_address="127.0.0.1",
            user_agent="test",
            device_fingerprint="device",
            policy=policy,
        )

    @staticmethod
    def _service(sessions, mfa_enabled=False):
        return LocalAuthenticationService(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUserFacade(),
            credential_repository=FakeCredentialRepository(mfa_enabled=mfa_enabled),
            auth_session_repository=sessions,
            mfa_challenge_store=RecordingMfaChallengeStore(),
            password_hasher=FakePasswordHasher(),
            token_service=FakeTokenService(),
            lockout_policy=LockoutPolicy(),
            session_expiry_policy=SessionExpiryPolicy(),
            mfa_policy=MfaPolicy(),
        )

    @staticmethod
    def _policy(
        *,
        context_type,
        knowledge_space_id,
        idle_timeout_minutes,
        absolute_timeout_minutes,
        require_mfa=False,
    ):
        return ResolvedAuthPolicy(
            context_type=context_type,
            knowledge_space_id=knowledge_space_id,
            auth_method=AuthProvider.LOCAL,
            tenant_id=None,
            require_mfa=require_mfa,
            idle_timeout_minutes=idle_timeout_minutes,
            absolute_timeout_minutes=absolute_timeout_minutes,
            reauthentication_minutes=(
                15 if context_type is AuthenticationContextType.MANAGEMENT else None
            ),
        )
