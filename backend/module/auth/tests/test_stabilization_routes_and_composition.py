import unittest

import httpx
from fastapi.routing import APIRoute

from bootstrap.database import async_session_factory
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
