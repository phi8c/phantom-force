from datetime import datetime, timezone
import unittest
from uuid import uuid4

from module.auth.application.dto.response.resolve_current_user_response import (
    ResolveCurrentUserResult,
)
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.authentication_context_guard import (
    AuthenticationContextGuard,
)
from module.auth.domain.entities.knowledge_space_auth_policy import (
    KnowledgeSpaceAuthPolicy,
)
from module.auth.domain.entities.management_auth_policy import ManagementAuthPolicy
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import (
    AuthenticationPolicyInactiveError,
    AuthenticationPolicyMissingError,
    InvalidAuthenticationContextError,
    KnowledgeSpaceContextMismatchError,
)
from module.knowledge_space.facade.dto import KnowledgeSpaceDTO


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubManagementPolicyRepository:
    def __init__(self, policy=None):
        self.policy = policy

    async def get_active(self):
        return self.policy


class StubKnowledgeSpacePolicyRepository:
    def __init__(self, policy=None):
        self.policy = policy

    async def get_by_knowledge_space_id(self, knowledge_space_id):
        return self.policy


class StubKnowledgeSpaceFacade:
    def __init__(self, knowledge_space=None):
        self.knowledge_space = knowledge_space

    async def get_knowledge_space(self, knowledge_space_id):
        return self.knowledge_space


class AuthPolicyResolverTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_management_policy_fails_closed(self) -> None:
        resolver = self._resolver()

        with self.assertRaises(AuthenticationPolicyMissingError):
            await resolver.resolve_management()

    async def test_inactive_knowledge_space_policy_fails_closed(self) -> None:
        knowledge_space_id = uuid4()
        policy = KnowledgeSpaceAuthPolicy(
            id=uuid4(),
            knowledge_space_id=knowledge_space_id,
            auth_method=AuthProvider.LOCAL,
            tenant_id=None,
            require_mfa=False,
            idle_timeout_minutes=30,
            absolute_timeout_minutes=480,
            is_active=False,
            created_by=None,
            created_at=NOW,
            updated_at=NOW,
        )
        resolver = self._resolver(
            knowledge_space_policy=policy,
            knowledge_space=KnowledgeSpaceDTO(
                id=knowledge_space_id,
                status="ACTIVE",
            ),
        )

        with self.assertRaises(AuthenticationPolicyInactiveError):
            await resolver.resolve_knowledge_space(knowledge_space_id)

    async def test_management_policy_resolves_management_context(self) -> None:
        policy = ManagementAuthPolicy(
            id=uuid4(),
            auth_method=AuthProvider.LOCAL,
            tenant_id=None,
            require_mfa=True,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
            reauthentication_minutes=15,
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )

        resolved = await self._resolver(management_policy=policy).resolve_management()

        self.assertEqual(resolved.context_type, AuthenticationContextType.MANAGEMENT)
        self.assertIsNone(resolved.knowledge_space_id)

    async def test_inactive_management_policy_fails_closed(self) -> None:
        policy = ManagementAuthPolicy(
            id=uuid4(),
            auth_method=AuthProvider.LOCAL,
            tenant_id=None,
            require_mfa=True,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
            reauthentication_minutes=15,
            is_active=False,
            created_at=NOW,
            updated_at=NOW,
        )

        with self.assertRaises(AuthenticationPolicyInactiveError):
            await self._resolver(management_policy=policy).resolve_management()

    @staticmethod
    def _resolver(
        management_policy=None,
        knowledge_space_policy=None,
        knowledge_space=None,
    ) -> AuthPolicyResolver:
        return AuthPolicyResolver(
            management_policy_repository=StubManagementPolicyRepository(
                management_policy
            ),
            knowledge_space_policy_repository=StubKnowledgeSpacePolicyRepository(
                knowledge_space_policy
            ),
            knowledge_space_facade=StubKnowledgeSpaceFacade(knowledge_space),
        )


class AuthenticationContextGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = AuthenticationContextGuard()
        self.knowledge_space_id = uuid4()

    def test_knowledge_space_session_is_rejected_by_management_guard(self) -> None:
        with self.assertRaises(InvalidAuthenticationContextError):
            self.guard.require_management(self._current_user(self.knowledge_space_id))

    def test_management_session_is_accepted_by_management_guard(self) -> None:
        current_user = self._current_user(None)
        current_user = ResolveCurrentUserResult(
            user_id=current_user.user_id,
            email=current_user.email,
            session_id=current_user.session_id,
            auth_method=current_user.auth_method,
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            authenticated_at=current_user.authenticated_at,
            mfa_verified_at=current_user.mfa_verified_at,
        )

        self.guard.require_management(current_user)

    def test_session_for_another_knowledge_space_is_rejected(self) -> None:
        with self.assertRaises(KnowledgeSpaceContextMismatchError):
            self.guard.require_knowledge_space(
                self._current_user(self.knowledge_space_id),
                uuid4(),
            )

    def test_session_for_same_knowledge_space_is_accepted(self) -> None:
        self.guard.require_knowledge_space(
            self._current_user(self.knowledge_space_id),
            self.knowledge_space_id,
        )

    @staticmethod
    def _current_user(knowledge_space_id) -> ResolveCurrentUserResult:
        return ResolveCurrentUserResult(
            user_id=uuid4(),
            email="user@example.com",
            session_id=uuid4(),
            auth_method=AuthProvider.LOCAL,
            context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
            knowledge_space_id=knowledge_space_id,
            authenticated_at=NOW,
            mfa_verified_at=None,
        )
