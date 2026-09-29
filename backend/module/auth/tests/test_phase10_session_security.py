from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from uuid import uuid4

from module.auth.application.dto.request.logout_request import LogoutRequest
from module.auth.application.dto.request.resolve_current_user_request import (
    ResolveCurrentUserRequest,
)
from module.auth.application.use_cases.logout import LogoutUseCase
from module.auth.application.use_cases.resolve_current_user import (
    ResolveCurrentUserUseCase,
)
from module.auth.domain.entities.auth_session import AuthSession
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import (
    SessionExpiredError,
    SessionInvalidError,
)
from module.auth.domain.services.reauthentication_policy import ReauthenticationPolicy
from module.auth.application.services.security_audit_service import SecurityAuditService
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.user.facade.dto import UserDTO


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUnitOfWork:
    def __init__(self):
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass


class FakeClock:
    def now(self):
        return NOW


class RecordingAuditRepository:
    def __init__(self):
        self.event = None

    async def add(self, event):
        self.event = event


class FakeTokens:
    def hash(self, raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()


class FakeSessions:
    def __init__(self, session):
        self.session = session
        self.updates = 0

    async def get_by_token_hash(self, token_hash):
        if self.session and self.session.session_token_hash == token_hash:
            return self.session
        return None

    async def update(self, session):
        self.session = session
        self.updates += 1


class FakeUsers:
    def __init__(self, user):
        self.user = user

    async def get_user(self, user_id):
        return self.user if self.user and self.user.id == user_id else None


class SessionSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_token_is_rejected(self) -> None:
        session = self._session()
        with self.assertRaises(SessionInvalidError):
            await self._resolver(session, self._user(session.user_id)).execute(
                ResolveCurrentUserRequest(raw_session_token="another-token")
            )

    async def test_security_audit_records_structured_event_without_token(self) -> None:
        repository = RecordingAuditRepository()
        audit = SecurityAuditService(repository, FakeClock())
        user_id = uuid4()

        await audit.record(
            "auth.session.created",
            actor_user_id=user_id,
            target_type="user",
            target_id=user_id,
            metadata={"method": "local"},
        )

        self.assertEqual(repository.event.action, "auth.session.created")
        self.assertEqual(repository.event.actor_user_id, user_id)
        self.assertNotIn("token", repository.event.metadata)

    async def test_valid_session_resolves_safe_context(self) -> None:
        session = self._session()
        use_case = self._resolver(session, self._user(session.user_id))

        result = await use_case.execute(
            ResolveCurrentUserRequest(raw_session_token="raw-token")
        )

        self.assertEqual(result.session_id, session.id)
        self.assertEqual(result.context_type, AuthenticationContextType.MANAGEMENT)
        self.assertFalse(hasattr(result, "session_token_hash"))

    async def test_idle_expiry_revokes_session(self) -> None:
        session = self._session(idle_expires_at=NOW)
        sessions = FakeSessions(session)
        use_case = self._resolver(session, self._user(session.user_id), sessions)

        with self.assertRaises(SessionExpiredError):
            await use_case.execute(
                ResolveCurrentUserRequest(raw_session_token="raw-token")
            )
        self.assertEqual(session.revoked_reason, "idle_timeout")

    async def test_absolute_expiry_revokes_session(self) -> None:
        session = self._session(absolute_expires_at=NOW)
        use_case = self._resolver(session, self._user(session.user_id))

        with self.assertRaises(SessionExpiredError):
            await use_case.execute(
                ResolveCurrentUserRequest(raw_session_token="raw-token")
            )
        self.assertEqual(session.revoked_reason, "absolute_timeout")

    async def test_revoked_session_is_rejected(self) -> None:
        session = self._session()
        session.revoked_at = NOW - timedelta(minutes=1)
        with self.assertRaises(SessionInvalidError):
            await self._resolver(session, self._user(session.user_id)).execute(
                ResolveCurrentUserRequest(raw_session_token="raw-token")
            )

    async def test_inactive_user_is_rejected(self) -> None:
        session = self._session()
        user = self._user(session.user_id, status="disabled")
        with self.assertRaises(SessionInvalidError):
            await self._resolver(session, user).execute(
                ResolveCurrentUserRequest(raw_session_token="raw-token")
            )

    async def test_logout_is_idempotent(self) -> None:
        session = self._session()
        sessions = FakeSessions(session)
        use_case = LogoutUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            token_service=FakeTokens(),
            auth_session_repository=sessions,
        )

        request = LogoutRequest(raw_session_token="raw-token")
        await use_case.execute(request)
        await use_case.execute(request)

        self.assertEqual(session.revoked_at, NOW)
        self.assertEqual(session.revoked_reason, "user_logout")
        self.assertEqual(sessions.updates, 1)

    def test_reauthentication_window_is_strictly_enforced(self) -> None:
        policy = ReauthenticationPolicy()
        self.assertTrue(
            policy.is_recently_authenticated(NOW - timedelta(minutes=14), NOW, 15)
        )
        self.assertFalse(
            policy.is_recently_authenticated(NOW - timedelta(minutes=15), NOW, 15)
        )

    @staticmethod
    def _resolver(session, user, sessions=None):
        return ResolveCurrentUserUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUsers(user),
            auth_session_repository=sessions or FakeSessions(session),
            token_service=FakeTokens(),
            session_expiry_policy=SessionExpiryPolicy(),
        )

    @staticmethod
    def _session(idle_expires_at=None, absolute_expires_at=None):
        return AuthSession.create(
            id=uuid4(),
            user_id=uuid4(),
            session_token_hash=FakeTokens().hash("raw-token"),
            auth_method=AuthProvider.LOCAL,
            context_type=AuthenticationContextType.MANAGEMENT,
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
            now=NOW - timedelta(minutes=1),
            idle_expires_at=idle_expires_at or NOW + timedelta(minutes=15),
            absolute_expires_at=absolute_expires_at or NOW + timedelta(hours=8),
        )

    @staticmethod
    def _user(user_id, status="active"):
        return UserDTO(
            id=user_id,
            email="user@example.com",
            status=status,
            full_name=None,
            email_verified=True,
        )
