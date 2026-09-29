from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import hashlib
import unittest
from uuid import uuid4

from module.auth.application.dto.response.verified_oidc_authentication import (
    VerifiedOidcAuthentication,
)
from module.auth.application.services.entra_authentication_service import (
    EntraAuthenticationService,
)
from module.auth.domain.entities.identity_link import IdentityLink
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import ExplicitAccountLinkRequiredError
from module.auth.domain.services.mfa_policy import MfaPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)
from module.auth.domain.value_objects.oidc_user_info import OidcUserInfo
from module.auth.presentation.redirects import append_auth_result
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
    def __init__(self, users=None):
        self.users = {user.id: user for user in (users or [])}

    async def get_user(self, user_id):
        return self.users.get(user_id)

    async def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u.email == email), None)

    async def create_user(self, email):
        user = UserDTO(
            id=uuid4(),
            email=email,
            status="pending_verification",
            full_name=None,
            email_verified=False,
        )
        self.users[user.id] = user
        return user

    async def mark_email_verified(self, user_id, verified_at):
        user = self.users[user_id]
        self.users[user_id] = UserDTO(
            id=user.id,
            email=user.email,
            status="active",
            full_name=user.full_name,
            email_verified=True,
        )

    async def activate_external_user(self, user_id, email_verified_at):
        user = self.users[user_id]
        self.users[user_id] = UserDTO(
            id=user.id,
            email=user.email,
            status="active",
            full_name=user.full_name,
            email_verified=email_verified_at is not None,
        )


class FakeIdentityLinks:
    def __init__(self, identity=None):
        self.identity = identity

    async def get_by_provider_and_sub(self, provider, external_sub):
        if (
            self.identity is not None
            and self.identity.provider is provider
            and self.identity.external_sub == external_sub
        ):
            return self.identity
        return None

    async def add(self, identity):
        self.identity = identity
        return identity


class FakeCredentials:
    def __init__(self, mfa_enabled=False):
        self.mfa_enabled = mfa_enabled

    async def get_by_user_id(self, user_id):
        if not self.mfa_enabled:
            return None
        return SimpleNamespace(mfa_enabled=True)


class RecordingSessions:
    def __init__(self):
        self.added = None

    async def add(self, session):
        self.added = session
        return session


class RecordingChallenges:
    def __init__(self):
        self.challenge = None

    async def create_challenge(self, challenge):
        self.challenge = challenge
        return "challenge-id"


class FakeTokens:
    def generate_raw_token(self):
        return "raw-session-token"

    def hash(self, raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()


class EntraAuthenticationTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_identity_creates_context_bound_session(self) -> None:
        user = self._user()
        identity = self._identity(user.id)
        sessions = RecordingSessions()
        service = self._service(
            users=FakeUsers([user]),
            identities=FakeIdentityLinks(identity),
            sessions=sessions,
        )

        result = await service.authenticate(
            self._verified(),
            ip_address="127.0.0.1",
            user_agent="test",
            device_fingerprint="device",
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.session_token, "raw-session-token")
        self.assertEqual(sessions.added.identity_link_id, identity.id)
        self.assertEqual(
            sessions.added.context_type,
            AuthenticationContextType.MANAGEMENT,
        )
        self.assertIsNone(sessions.added.knowledge_space_id)

    async def test_unlinked_identity_provisions_new_verified_user_and_link(self) -> None:
        users = FakeUsers()
        identities = FakeIdentityLinks()
        sessions = RecordingSessions()
        service = self._service(users, identities, sessions)

        await service.authenticate(
            self._verified(),
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
        )

        provisioned = next(iter(users.users.values()))
        self.assertEqual(provisioned.status, "active")
        self.assertFalse(provisioned.email_verified)
        self.assertEqual(identities.identity.user_id, provisioned.id)
        self.assertEqual(sessions.added.identity_link_id, identities.identity.id)

    async def test_matching_email_is_not_automatically_linked(self) -> None:
        existing_local_user = self._user(email="entra@example.com")
        service = self._service(
            users=FakeUsers([existing_local_user]),
            identities=FakeIdentityLinks(),
            sessions=RecordingSessions(),
        )

        with self.assertRaises(ExplicitAccountLinkRequiredError):
            await service.authenticate(
                self._verified(),
                ip_address=None,
                user_agent=None,
                device_fingerprint=None,
            )

    async def test_knowledge_space_session_preserves_scope_and_identity(self) -> None:
        user = self._user()
        identity = self._identity(user.id)
        sessions = RecordingSessions()
        knowledge_space_id = uuid4()
        service = self._service(
            users=FakeUsers([user]),
            identities=FakeIdentityLinks(identity),
            sessions=sessions,
        )

        await service.authenticate(
            self._verified(
                context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
                knowledge_space_id=knowledge_space_id,
            ),
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
        )

        self.assertEqual(sessions.added.knowledge_space_id, knowledge_space_id)
        self.assertEqual(sessions.added.identity_link_id, identity.id)

    async def test_mfa_challenge_keeps_identity_and_knowledge_space_context(self) -> None:
        user = self._user()
        identity = self._identity(user.id)
        challenges = RecordingChallenges()
        knowledge_space_id = uuid4()
        service = self._service(
            users=FakeUsers([user]),
            identities=FakeIdentityLinks(identity),
            sessions=RecordingSessions(),
            credentials=FakeCredentials(mfa_enabled=True),
            challenges=challenges,
        )

        result = await service.authenticate(
            self._verified(
                context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
                knowledge_space_id=knowledge_space_id,
                require_mfa=True,
            ),
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
        )

        self.assertEqual(result.status, "mfa_required")
        self.assertEqual(challenges.challenge.identity_link_id, identity.id)
        self.assertEqual(challenges.challenge.knowledge_space_id, knowledge_space_id)

    def test_redirect_only_extends_configured_destination(self) -> None:
        result = append_auth_result(
            "https://frontend.example/auth/complete?source=entra",
            "mfa_required",
            "challenge-id",
        )
        self.assertEqual(
            result,
            "https://frontend.example/auth/complete?source=entra&auth_status=mfa_required&mfa_challenge_id=challenge-id",
        )

    @staticmethod
    def _service(
        users,
        identities,
        sessions,
        credentials=None,
        challenges=None,
    ):
        return EntraAuthenticationService(
            uow=FakeUnitOfWork(),
            clock=FakeClock(),
            users=users,
            identity_links=identities,
            credentials=credentials or FakeCredentials(),
            sessions=sessions,
            mfa_challenges=challenges or RecordingChallenges(),
            tokens=FakeTokens(),
            session_expiry=SessionExpiryPolicy(),
            mfa=MfaPolicy(),
        )

    @staticmethod
    def _user(email="entra@example.com"):
        return UserDTO(
            id=uuid4(),
            email=email,
            status="active",
            full_name=None,
            email_verified=True,
        )

    @staticmethod
    def _identity(user_id):
        return IdentityLink(
            id=uuid4(),
            user_id=user_id,
            provider=AuthProvider.ENTRA,
            external_sub="external-sub",
            tenant_id="tenant-id",
            email_at_link="entra@example.com",
            linked_at=NOW,
        )

    @staticmethod
    def _verified(
        context_type=AuthenticationContextType.MANAGEMENT,
        knowledge_space_id=None,
        require_mfa=False,
    ):
        return VerifiedOidcAuthentication(
            transaction=OidcAuthorizationTransaction(
                context_type=context_type,
                knowledge_space_id=knowledge_space_id,
                expected_tenant_id="tenant-id",
                nonce="nonce",
                code_verifier="verifier",
                require_mfa=require_mfa,
                idle_timeout_minutes=15,
                absolute_timeout_minutes=480,
                created_at=NOW,
                expires_at=NOW + timedelta(minutes=10),
            ),
            user_info=OidcUserInfo(
                external_sub="external-sub",
                email="entra@example.com",
                email_verified=False,
                tenant_id="tenant-id",
            ),
        )
