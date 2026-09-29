import base64
from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from unittest.mock import patch
from uuid import uuid4

from module.auth.application.dto.request.verify_mfa_request import VerifyMfaRequest
from module.auth.application.use_cases.verify_mfa import VerifyMfaUseCase
from module.auth.domain.entities.credential import Credential
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import InvalidMfaChallengeError
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.value_objects.mfa_challenge import MfaChallenge
from module.auth.infrastructure.mfa.in_memory_challenge_store import (
    InMemoryMfaChallengeStore,
)
from module.auth.infrastructure.mfa.totp_provider import TotpMfaProvider
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


class FakeUsers:
    def __init__(self, user_id):
        self.user = UserDTO(
            id=user_id,
            email="user@example.com",
            status="active",
            full_name=None,
            email_verified=True,
        )

    async def get_user(self, user_id):
        return self.user if user_id == self.user.id else None


class FakeCredentials:
    def __init__(self, user_id):
        self.credential = Credential(
            user_id=user_id,
            password_hash="hash",
            password_algo="test",
            password_changed_at=NOW,
            failed_attempts=0,
            locked_until=None,
            mfa_enabled=True,
            mfa_secret_encrypted="encrypted-secret",
            created_at=NOW,
            updated_at=NOW,
        )

    async def get_by_user_id(self, user_id):
        return self.credential if user_id == self.credential.user_id else None


class FakeEncryptor:
    async def decrypt(self, ciphertext):
        return "totp-secret"


class FakeMfaProvider:
    def verify_totp(self, secret, code):
        return secret == "totp-secret" and code == "123456"


class FakeTokens:
    def generate_raw_token(self):
        return "session-token"

    def hash(self, raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()


class RecordingSessions:
    def __init__(self):
        self.added = None

    async def add(self, session):
        self.added = session
        return session


class MfaChallengeStoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_challenge_can_only_be_taken_once(self) -> None:
        store = InMemoryMfaChallengeStore()
        challenge = self._challenge()
        challenge_id = await store.create_challenge(challenge)

        self.assertEqual(await store.take_challenge(challenge_id, NOW), challenge)
        self.assertIsNone(await store.take_challenge(challenge_id, NOW))

    async def test_expired_challenge_is_rejected(self) -> None:
        store = InMemoryMfaChallengeStore()
        challenge = self._challenge(expires_at=NOW - timedelta(seconds=1))
        challenge_id = await store.create_challenge(challenge)

        self.assertIsNone(await store.take_challenge(challenge_id, NOW))

    @staticmethod
    def _challenge(expires_at=None):
        return MfaChallenge(
            user_id=uuid4(),
            auth_method=AuthProvider.LOCAL,
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
            created_at=NOW,
            expires_at=expires_at or NOW + timedelta(minutes=5),
        )


class VerifyMfaTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_creates_assured_session_and_prevents_replay(self) -> None:
        user_id = uuid4()
        knowledge_space_id = uuid4()
        store = InMemoryMfaChallengeStore()
        challenge_id = await store.create_challenge(
            MfaChallenge(
                user_id=user_id,
                auth_method=AuthProvider.LOCAL,
                context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
                knowledge_space_id=knowledge_space_id,
                idle_timeout_minutes=30,
                absolute_timeout_minutes=240,
                ip_address="127.0.0.1",
                user_agent="test",
                device_fingerprint="device",
                created_at=NOW,
                expires_at=NOW + timedelta(minutes=5),
            )
        )
        sessions = RecordingSessions()
        use_case = VerifyMfaUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUsers(user_id),
            credential_repository=FakeCredentials(user_id),
            auth_session_repository=sessions,
            challenge_store=store,
            mfa_provider=FakeMfaProvider(),
            encryptor=FakeEncryptor(),
            token_service=FakeTokens(),
            session_expiry_policy=SessionExpiryPolicy(),
        )

        result = await use_case.execute(
            VerifyMfaRequest(challenge_id=challenge_id, code="123456")
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(sessions.added.mfa_verified_at, NOW)
        self.assertEqual(sessions.added.knowledge_space_id, knowledge_space_id)
        with self.assertRaises(InvalidMfaChallengeError):
            await use_case.execute(
                VerifyMfaRequest(challenge_id=challenge_id, code="123456")
            )

    async def test_invalid_code_does_not_create_session(self) -> None:
        user_id = uuid4()
        store = InMemoryMfaChallengeStore()
        challenge_id = await store.create_challenge(
            MfaChallenge(
                user_id=user_id,
                auth_method=AuthProvider.LOCAL,
                context_type=AuthenticationContextType.MANAGEMENT,
                knowledge_space_id=None,
                idle_timeout_minutes=15,
                absolute_timeout_minutes=480,
                ip_address=None,
                user_agent=None,
                device_fingerprint=None,
                created_at=NOW,
                expires_at=NOW + timedelta(minutes=5),
            )
        )
        sessions = RecordingSessions()
        use_case = VerifyMfaUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUsers(user_id),
            credential_repository=FakeCredentials(user_id),
            auth_session_repository=sessions,
            challenge_store=store,
            mfa_provider=FakeMfaProvider(),
            encryptor=FakeEncryptor(),
            token_service=FakeTokens(),
            session_expiry_policy=SessionExpiryPolicy(),
        )

        with self.assertRaises(InvalidMfaChallengeError):
            await use_case.execute(
                VerifyMfaRequest(challenge_id=challenge_id, code="000000")
            )
        self.assertIsNone(sessions.added)


class TotpProviderTests(unittest.TestCase):
    def test_matches_rfc_6238_sha1_vector(self) -> None:
        secret = base64.b32encode(b"12345678901234567890").decode("ascii")
        provider = TotpMfaProvider(issuer="test", digits=8)

        with patch("module.auth.infrastructure.mfa.totp_provider.time.time", return_value=59):
            self.assertTrue(provider.verify_totp(secret, "94287082"))
