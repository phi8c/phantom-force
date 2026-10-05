from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from uuid import uuid4

from module.auth.application.dto.request.register_local_user_request import (
    RegisterLocalUserRequest,
)
from module.auth.application.dto.request.verify_email_request import VerifyEmailRequest
from module.auth.application.use_cases.register_local_user import RegisterLocalUserUseCase
from module.auth.application.use_cases.verify_email import VerifyEmailUseCase
from module.auth.domain.entities.verification_token import VerificationToken
from module.auth.domain.enums.token_purpose import TokenPurpose
from module.auth.domain.exception.exceptions import (
    ExpiredVerificationTokenError,
    InvalidVerificationTokenError,
)
from module.auth.domain.services.password_policy import PasswordPolicy
from module.auth.domain.services.verification_token_policy import VerificationTokenPolicy
from module.auth.infrastructure.email.console_verification_email_sender import (
    ConsoleVerificationEmailSender,
)
from module.user.facade.dto import UserDTO


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUnitOfWork:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.rollbacks += 1

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class FakeClock:
    def now(self):
        return NOW


class FakeTokenService:
    raw_token = "a" * 48

    def generate_raw_token(self):
        return self.raw_token

    def hash(self, raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()


class FakePasswordHasher:
    algorithm_name = "test"

    def hash(self, password):
        return f"hashed:{password}"


class FakeUserFacade:
    def __init__(self, existing=None):
        self.existing = existing
        self.created = None
        self.verified = None

    async def get_user_by_email(self, email):
        return self.existing

    async def create_user(self, email):
        self.created = UserDTO(
            id=uuid4(),
            email=email,
            status="pending_verification",
            full_name=None,
            email_verified=False,
        )
        return self.created

    async def mark_email_verified(self, user_id, verified_at):
        self.verified = (user_id, verified_at)


class FakeCredentialRepository:
    def __init__(self):
        self.added = None

    async def add(self, credential):
        self.added = credential
        return credential


class FakeVerificationTokenRepository:
    def __init__(self, token=None):
        self.token = token
        self.added = None

    async def add(self, token):
        self.added = token
        self.token = token
        return token

    async def get_by_token_hash_for_update(self, token_hash):
        if self.token and self.token.token_hash == token_hash:
            return self.token
        return None

    async def update(self, token):
        self.token = token


class RecordingEmailSender:
    def __init__(self):
        self.sent = None

    async def send_verification_email(self, recipient, raw_token):
        self.sent = (recipient, raw_token)


class LocalRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_console_sender_logs_verification_link(self) -> None:
        sender = ConsoleVerificationEmailSender(
            verification_url="http://localhost:3000/verify-email",
        )

        with self.assertLogs(
            "module.auth.infrastructure.email.console_verification_email_sender",
            level="WARNING",
        ) as captured:
            await sender.send_verification_email(
                "user@example.com",
                "raw token",
            )

        self.assertIn("recipient=user@example.com", captured.output[0])
        self.assertIn("token=raw+token", captured.output[0])

    async def test_register_stores_only_hash_and_dispatches_email(self) -> None:
        uow = FakeUnitOfWork()
        users = FakeUserFacade()
        credentials = FakeCredentialRepository()
        tokens = FakeVerificationTokenRepository()
        sender = RecordingEmailSender()
        token_service = FakeTokenService()
        use_case = RegisterLocalUserUseCase(
            uow=uow,
            clock=FakeClock(),
            user_facade=users,
            credential_repository=credentials,
            verification_token_repository=tokens,
            password_hasher=FakePasswordHasher(),
            password_policy=PasswordPolicy(),
            verification_token_policy=VerificationTokenPolicy(),
            token_service=token_service,
            verification_email_sender=sender,
        )

        result = await use_case.execute(
            RegisterLocalUserRequest(
                email="user@example.com",
                password="long-password",
            )
        )

        self.assertEqual(uow.commits, 1)
        self.assertEqual(sender.sent, ("user@example.com", token_service.raw_token))
        self.assertEqual(tokens.added.token_hash, token_service.hash(token_service.raw_token))
        self.assertNotEqual(tokens.added.token_hash, token_service.raw_token)
        self.assertFalse(hasattr(result, "raw_verification_token"))

    async def test_duplicate_registration_has_same_public_result(self) -> None:
        existing = UserDTO(
            id=uuid4(),
            email="user@example.com",
            status="active",
            full_name=None,
            email_verified=True,
        )
        sender = RecordingEmailSender()
        use_case = RegisterLocalUserUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUserFacade(existing=existing),
            credential_repository=FakeCredentialRepository(),
            verification_token_repository=FakeVerificationTokenRepository(),
            password_hasher=FakePasswordHasher(),
            password_policy=PasswordPolicy(),
            verification_token_policy=VerificationTokenPolicy(),
            token_service=FakeTokenService(),
            verification_email_sender=sender,
        )

        result = await use_case.execute(
            RegisterLocalUserRequest(
                email="user@example.com",
                password="long-password",
            )
        )

        self.assertIn("email", result.message.lower())
        self.assertIsNone(sender.sent)


class VerifyEmailTests(unittest.IsolatedAsyncioTestCase):
    async def test_verification_is_one_time_and_marks_user_verified(self) -> None:
        raw_token = FakeTokenService.raw_token
        token_service = FakeTokenService()
        token = self._token(
            token_hash=token_service.hash(raw_token),
            expires_at=NOW + timedelta(minutes=5),
        )
        repository = FakeVerificationTokenRepository(token)
        users = FakeUserFacade()
        use_case = VerifyEmailUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=users,
            verification_token_repository=repository,
            token_service=token_service,
        )

        await use_case.execute(VerifyEmailRequest(raw_token=raw_token))

        self.assertEqual(users.verified, (token.user_id, NOW))
        self.assertEqual(repository.token.used_at, NOW)
        with self.assertRaises(InvalidVerificationTokenError):
            await use_case.execute(VerifyEmailRequest(raw_token=raw_token))

    async def test_expired_verification_token_is_rejected(self) -> None:
        raw_token = FakeTokenService.raw_token
        token_service = FakeTokenService()
        repository = FakeVerificationTokenRepository(
            self._token(
                token_hash=token_service.hash(raw_token),
                expires_at=NOW - timedelta(seconds=1),
            )
        )
        use_case = VerifyEmailUseCase(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            user_facade=FakeUserFacade(),
            verification_token_repository=repository,
            token_service=token_service,
        )

        with self.assertRaises(ExpiredVerificationTokenError):
            await use_case.execute(VerifyEmailRequest(raw_token=raw_token))

    @staticmethod
    def _token(token_hash, expires_at):
        return VerificationToken(
            id=uuid4(),
            user_id=uuid4(),
            token_hash=token_hash,
            purpose=TokenPurpose.EMAIL_VERIFY,
            expires_at=expires_at,
            used_at=None,
            created_at=NOW,
        )
