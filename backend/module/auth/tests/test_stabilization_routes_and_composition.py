import unittest
from contextlib import asynccontextmanager
from importlib import import_module
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi import Response
from fastapi.routing import APIRoute

from bootstrap.database import async_session_factory, session_scope
from module.auth.application.dto.response.local_login_response import LocalLoginResult
from module.auth.composition.factory import create_auth_foundation
from module.auth.composition.runtime import create_auth_runtime
from module.auth.infrastructure.oidc.microsoft_entra_oidc_provider import (
    MicrosoftEntraOidcProvider,
)
from module.auth.infrastructure.persistence.repositories.auth_session_repository_impl import (
    AuthSessionRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.credential_repository_impl import (
    CredentialRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.identity_link_repository_impl import (
    IdentityLinkRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.knowledge_space_auth_policy_repository_impl import (
    KnowledgeSpaceAuthPolicyRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.management_auth_policy_repository_impl import (
    ManagementAuthPolicyRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.verification_token_repository_impl import (
    VerificationTokenRepositoryImpl,
)
from module.auth.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from module.auth.presentation.controller.auth_controller import router
from module.auth.presentation.controller.auth_controller import _set_session_cookie
from module.auth.presentation.dependencies.auth_dependencies import (
    get_current_user,
)
from module.auth.presentation.dependencies.providers import (
    get_auth_frontend_redirect_url,
    get_authentication_context_guard,
)
from module.auth.presentation.dependencies.use_case_providers import (
    get_complete_oidc_use_case,
)
from module.auth.application.dto.response.resolve_current_user_response import (
    ResolveCurrentUserResult,
)
from module.auth.application.services.authentication_context_guard import (
    AuthenticationContextGuard,
)
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.contracts.system_clock import SystemClock
from module.knowledge_space.facade.contract import KnowledgeSpaceModuleFacade
from module.user.facade.contract import UserModuleFacade


EXPECTED_AUTH_ROUTES = {
    ("POST", "/auth/register"),
    ("POST", "/auth/verify-email"),
    ("POST", "/auth/management/login/local"),
    ("POST", "/auth/management/login/entra/start"),
    ("GET", "/auth/knowledge-spaces/{knowledge_space_id}/requirement"),
    ("POST", "/auth/knowledge-spaces/{knowledge_space_id}/login/local"),
    ("POST", "/auth/knowledge-spaces/{knowledge_space_id}/login/entra/start"),
    ("GET", "/auth/entra/callback"),
    ("POST", "/auth/mfa/verify"),
    ("GET", "/auth/me"),
    ("POST", "/auth/logout"),
    ("POST", "/auth/logout-all"),
}


class AuthRouteRegistrationTests(unittest.TestCase):
    def test_auth_route_inventory_matches_public_contract(self) -> None:
        registered = {
            (method, route.path)
            for route in router.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        }

        self.assertEqual(registered, EXPECTED_AUTH_ROUTES)

    def test_each_method_and_path_pair_is_unique(self) -> None:
        registered = [
            (method, route.path)
            for route in router.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        ]

        self.assertEqual(len(registered), len(set(registered)))


class AuthCompositionSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_fastapi_application_lifespan_initializes_auth_runtime(self) -> None:
        from main import app

        async with app.router.lifespan_context(app):
            self.assertIsNotNone(app.state.auth_mfa_challenge_store)
            self.assertIsNotNone(app.state.auth_oidc_transaction_store)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                health = await client.get("/health")
                management = await client.get("/enterprises")
                knowledge_space = await client.post(
                    "/chat",
                    json={
                        "knowledge_space_id": "00000000-0000-0000-0000-000000000001",
                        "question": "test",
                    },
                )

            self.assertEqual(health.status_code, 200)
            self.assertEqual(management.status_code, 401)
            self.assertEqual(knowledge_space.status_code, 401)

        self.assertFalse(hasattr(app.state, "auth_mfa_challenge_store"))
        self.assertFalse(hasattr(app.state, "auth_oidc_transaction_store"))

    async def test_chat_enforces_knowledge_space_context_before_business_logic(self):
        from main import app

        requested_space_id = uuid4()
        business_logic_reached = False

        @asynccontextmanager
        async def stop_before_chat_dependencies():
            nonlocal business_logic_reached
            business_logic_reached = True
            raise RuntimeError("chat-business-logic-reached")
            yield

        async def request_as(current_user, knowledge_space_id):
            app.dependency_overrides[get_current_user] = lambda: current_user
            app.dependency_overrides[get_authentication_context_guard] = (
                AuthenticationContextGuard
            )
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://testserver",
                ) as client:
                    return await client.post(
                        "/chat",
                        json={
                            "knowledge_space_id": str(knowledge_space_id),
                            "question": "test",
                        },
                    )
            finally:
                app.dependency_overrides.clear()

        management = self._current_user(
            AuthenticationContextType.MANAGEMENT,
            None,
        )
        response = await request_as(management, requested_space_id)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(business_logic_reached)

        another_space = uuid4()
        knowledge_space_user = self._current_user(
            AuthenticationContextType.KNOWLEDGE_SPACE,
            requested_space_id,
        )
        response = await request_as(knowledge_space_user, another_space)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(business_logic_reached)

        chat_router_module = import_module("module.chats.chat.presentation.router")
        with patch.object(
            chat_router_module,
            "session_scope",
            stop_before_chat_dependencies,
        ):
            with self.assertRaisesRegex(RuntimeError, "chat-business-logic-reached"):
                await request_as(knowledge_space_user, requested_space_id)
        self.assertTrue(business_logic_reached)

    def test_session_cookie_security_attributes_are_stable(self) -> None:
        response = Response()
        _set_session_cookie(response, "opaque-session-token")

        cookie = response.headers["set-cookie"]
        self.assertIn("__Host-session=opaque-session-token", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("Path=/", cookie)
        self.assertIn("SameSite=strict", cookie)

    async def test_entra_callback_uses_trusted_redirect_and_sets_session(self) -> None:
        from main import app

        class SuccessfulOidcUseCase:
            async def execute(self, request):
                return LocalLoginResult(
                    status="success",
                    session_token="opaque-session-token",
                )

        app.dependency_overrides[get_complete_oidc_use_case] = SuccessfulOidcUseCase
        app.dependency_overrides[get_auth_frontend_redirect_url] = (
            lambda: "https://frontend.example/auth/callback"
        )
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                response = await client.get(
                    "/auth/entra/callback",
                    params={
                        "state": "server-state",
                        "code": "authorization-code",
                        "redirect_url": "https://attacker.example",
                    },
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "https://frontend.example/auth/callback?auth_status=success",
        )
        self.assertNotIn("attacker.example", response.headers["location"])
        self.assertIn("__Host-session=opaque-session-token", response.headers["set-cookie"])

    async def test_entra_callback_mfa_result_does_not_set_session(self) -> None:
        from main import app

        class MfaOidcUseCase:
            async def execute(self, request):
                return LocalLoginResult(
                    status="mfa_required",
                    mfa_challenge_id="challenge-id",
                )

        app.dependency_overrides[get_complete_oidc_use_case] = MfaOidcUseCase
        app.dependency_overrides[get_auth_frontend_redirect_url] = (
            lambda: "https://frontend.example/auth/callback"
        )
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                response = await client.get(
                    "/auth/entra/callback",
                    params={"state": "server-state", "code": "authorization-code"},
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "https://frontend.example/auth/callback"
            "?auth_status=mfa_required&mfa_challenge_id=challenge-id",
        )
        self.assertNotIn("set-cookie", response.headers)

    async def test_session_scope_closes_without_implicit_commit_on_exception(self):
        events = []

        class FakeSession:
            async def commit(self):
                events.append("commit")

        class FakeSessionContext:
            async def __aenter__(self):
                events.append("enter")
                return FakeSession()

            async def __aexit__(self, exc_type, exc, traceback):
                events.append(("exit", exc_type))

        with patch("bootstrap.database.async_session_factory", FakeSessionContext):
            with self.assertRaisesRegex(RuntimeError, "request-failed"):
                async with session_scope():
                    raise RuntimeError("request-failed")

        self.assertEqual(events, ["enter", ("exit", RuntimeError)])

    async def test_real_fastapi_auth_graph_can_be_constructed(self) -> None:
        async with async_session_factory() as session:
            foundation = create_auth_foundation(session)

            self.assertIsInstance(
                foundation.auth_session_repository,
                AuthSessionRepositoryImpl,
            )
            self.assertIsInstance(
                foundation.identity_link_repository,
                IdentityLinkRepositoryImpl,
            )
            self.assertIsInstance(
                foundation.credential_repository,
                CredentialRepositoryImpl,
            )
            self.assertIsInstance(
                foundation.verification_token_repository,
                VerificationTokenRepositoryImpl,
            )
            self.assertIsInstance(
                foundation.knowledge_space_auth_policy_repository,
                KnowledgeSpaceAuthPolicyRepositoryImpl,
            )
            self.assertIsInstance(
                foundation.management_auth_policy_repository,
                ManagementAuthPolicyRepositoryImpl,
            )
            self.assertIsInstance(foundation.unit_of_work, SqlAlchemyUnitOfWork)
            self.assertIsInstance(
                foundation.oidc_provider,
                MicrosoftEntraOidcProvider,
            )
            self.assertIsInstance(foundation.user_facade, UserModuleFacade)
            self.assertIsInstance(
                foundation.knowledge_space_facade,
                KnowledgeSpaceModuleFacade,
            )
            self.assertIsNotNone(foundation.security_audit)
            self.assertIsNotNone(foundation.token_service)
            self.assertIsNotNone(foundation.mfa_provider)

        runtime = create_auth_runtime()
        self.assertIsNotNone(runtime.mfa_challenge_store)
        self.assertIsNotNone(runtime.oidc_transaction_store)

    @staticmethod
    def _current_user(context_type, knowledge_space_id):
        now = SystemClock().now()
        return ResolveCurrentUserResult(
            user_id=uuid4(),
            email="user@example.com",
            session_id=uuid4(),
            auth_method=AuthProvider.LOCAL,
            context_type=context_type,
            knowledge_space_id=knowledge_space_id,
            authenticated_at=now,
            mfa_verified_at=None,
        )
