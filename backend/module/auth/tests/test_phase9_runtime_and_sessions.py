from datetime import datetime, timezone
import unittest
from uuid import uuid4

from module.auth.application.dto.request.logout_all_sessions_request import (
    LogoutAllSessionsRequest,
)
from module.auth.application.use_cases.logout_all_session import (
    LogoutAllSessionsUseCase,
)
from module.auth.composition.runtime import create_auth_runtime
from module.auth.infrastructure.mfa.in_memory_challenge_store import (
    InMemoryMfaChallengeStore,
)
from module.auth.infrastructure.oidc.in_memory_transaction_store import (
    InMemoryOidcTransactionStore,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUnitOfWork:
    def __init__(self):
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class FakeClock:
    def now(self):
        return NOW


class RecordingSessions:
    def __init__(self):
        self.revocation = None

    async def revoke_all_by_user_id(self, user_id, revoked_at, revoked_reason):
        self.revocation = (user_id, revoked_at, revoked_reason)


class AuthRuntimeTests(unittest.TestCase):
    def test_runtime_owns_fresh_process_local_security_stores(self) -> None:
        first = create_auth_runtime()
        second = create_auth_runtime()

        self.assertIsInstance(first.mfa_challenge_store, InMemoryMfaChallengeStore)
        self.assertIsInstance(
            first.oidc_transaction_store,
            InMemoryOidcTransactionStore,
        )
        self.assertIsNot(first.mfa_challenge_store, second.mfa_challenge_store)
        self.assertIsNot(first.oidc_transaction_store, second.oidc_transaction_store)


class LogoutAllSessionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_revokes_all_contexts_for_canonical_user(self) -> None:
        user_id = uuid4()
        uow = FakeUnitOfWork()
        sessions = RecordingSessions()
        use_case = LogoutAllSessionsUseCase(
            uow=uow,
            clock=FakeClock(),
            auth_session_repository=sessions,
        )

        await use_case.execute(LogoutAllSessionsRequest(user_id=user_id))

        self.assertEqual(
            sessions.revocation,
            (user_id, NOW, "user_logout_all"),
        )
        self.assertTrue(uow.committed)
