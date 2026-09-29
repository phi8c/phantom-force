import base64
from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from module.auth.application.dto.response.resolved_auth_policy import ResolvedAuthPolicy
from module.auth.application.services.oidc_authentication_service import (
    OidcAuthenticationService,
)
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import (
    OidcStateInvalidError,
    OidcTenantMismatchError,
    OidcTokenValidationError,
    OidcTransactionExpiredError,
)
from module.auth.domain.value_objects.oidc_authorization_transaction import (
    OidcAuthorizationTransaction,
)
from module.auth.domain.value_objects.oidc_user_info import OidcUserInfo
from module.auth.infrastructure.oidc.in_memory_transaction_store import (
    InMemoryOidcTransactionStore,
)
from module.auth.infrastructure.oidc.microsoft_entra_oidc_provider import (
    MicrosoftEntraOidcProvider,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return NOW


class RecordingOidcProvider:
    def __init__(self):
        self.start = None
        self.exchange = None

    def build_authorization_url(self, **kwargs):
        self.start = kwargs
        return "https://login.example/authorize?state=" + kwargs["state"]

    async def exchange_code_and_verify(self, **kwargs):
        self.exchange = kwargs
        return OidcUserInfo(
            external_sub="external-object-id",
            email="user@example.com",
            email_verified=True,
            tenant_id=kwargs["expected_tenant_id"],
        )


class OidcTransactionStoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_state_is_one_time_and_not_stored_in_plaintext(self) -> None:
        store = InMemoryOidcTransactionStore()
        transaction = self._transaction()
        state = await store.create_transaction(transaction)

        self.assertNotIn(state, store._transactions)
        self.assertEqual(await store.take_transaction(state, NOW), transaction)
        with self.assertRaises(OidcStateInvalidError):
            await store.take_transaction(state, NOW)

    async def test_expired_transaction_is_rejected_and_consumed(self) -> None:
        store = InMemoryOidcTransactionStore()
        state = await store.create_transaction(
            self._transaction(expires_at=NOW - timedelta(seconds=1))
        )

        with self.assertRaises(OidcTransactionExpiredError):
            await store.take_transaction(state, NOW)
        with self.assertRaises(OidcStateInvalidError):
            await store.take_transaction(state, NOW)

    @staticmethod
    def _transaction(expires_at=None):
        return OidcAuthorizationTransaction(
            context_type=AuthenticationContextType.MANAGEMENT,
            knowledge_space_id=None,
            expected_tenant_id="tenant-id",
            nonce="nonce",
            code_verifier="verifier",
            require_mfa=False,
            idle_timeout_minutes=15,
            absolute_timeout_minutes=480,
            created_at=NOW,
            expires_at=expires_at or NOW + timedelta(minutes=10),
        )


class OidcAuthenticationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_and_complete_preserve_security_bindings(self) -> None:
        provider = RecordingOidcProvider()
        store = InMemoryOidcTransactionStore()
        service = OidcAuthenticationService(FakeClock(), provider, store)
        knowledge_space_id = uuid4()
        policy = ResolvedAuthPolicy(
            context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
            knowledge_space_id=knowledge_space_id,
            auth_method=AuthProvider.ENTRA,
            tenant_id="tenant-id",
            require_mfa=True,
            idle_timeout_minutes=30,
            absolute_timeout_minutes=240,
            reauthentication_minutes=None,
        )

        started = await service.start(policy)
        state = parse_qs(urlparse(started.authorization_url).query)["state"][0]
        completed = await service.complete(state=state, code="authorization-code")

        self.assertEqual(provider.start["expected_tenant_id"], "tenant-id")
        self.assertTrue(provider.start["nonce"])
        self.assertTrue(provider.start["code_challenge"])
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(
                completed.transaction.code_verifier.encode("ascii")
            ).digest()
        ).decode("ascii").rstrip("=")
        self.assertEqual(provider.start["code_challenge"], expected_challenge)
        self.assertEqual(provider.exchange["expected_nonce"], provider.start["nonce"])
        self.assertEqual(provider.exchange["code_verifier"], completed.transaction.code_verifier)
        self.assertEqual(completed.transaction.knowledge_space_id, knowledge_space_id)
        self.assertTrue(completed.transaction.require_mfa)


class MicrosoftEntraClaimValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MicrosoftEntraOidcProvider(
            client_id="client-id",
            client_secret="secret",
            redirect_uri="https://api.example/auth/callback",
        )
        self.claims = {
            "iss": "https://login.microsoftonline.com/tenant-id/v2.0",
            "aud": "client-id",
            "exp": int((NOW + timedelta(minutes=5)).timestamp()),
            "nbf": int((NOW - timedelta(minutes=1)).timestamp()),
            "nonce": "nonce",
            "tid": "tenant-id",
        }

    def test_valid_claims_are_accepted(self) -> None:
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ):
            self.provider._validate_claims(
                self.claims,
                expected_issuer=self.claims["iss"],
                expected_tenant_id="tenant-id",
                expected_nonce="nonce",
            )

    def test_wrong_tenant_is_rejected_explicitly(self) -> None:
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ), self.assertRaises(OidcTenantMismatchError):
            self.provider._validate_claims(
                self.claims,
                expected_issuer=self.claims["iss"],
                expected_tenant_id="another-tenant",
                expected_nonce="nonce",
            )

    def test_wrong_nonce_is_rejected(self) -> None:
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ), self.assertRaises(OidcTokenValidationError):
            self.provider._validate_claims(
                self.claims,
                expected_issuer=self.claims["iss"],
                expected_tenant_id="tenant-id",
                expected_nonce="another-nonce",
            )

    def test_wrong_issuer_is_rejected(self) -> None:
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ), self.assertRaises(OidcTokenValidationError):
            self.provider._validate_claims(
                self.claims,
                expected_issuer="https://issuer.example/another-tenant",
                expected_tenant_id="tenant-id",
                expected_nonce="nonce",
            )

    def test_wrong_audience_is_rejected(self) -> None:
        claims = {**self.claims, "aud": "another-client"}
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ), self.assertRaises(OidcTokenValidationError):
            self.provider._validate_claims(
                claims,
                expected_issuer=claims["iss"],
                expected_tenant_id="tenant-id",
                expected_nonce="nonce",
            )

    def test_expired_token_is_rejected(self) -> None:
        claims = {**self.claims, "exp": int((NOW - timedelta(seconds=1)).timestamp())}
        with patch(
            "module.auth.infrastructure.oidc.microsoft_entra_oidc_provider.time.time",
            return_value=NOW.timestamp(),
        ), self.assertRaises(OidcTokenValidationError):
            self.provider._validate_claims(
                claims,
                expected_issuer=claims["iss"],
                expected_tenant_id="tenant-id",
                expected_nonce="nonce",
            )

    def test_signature_is_verified_against_matching_jwk(self) -> None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_numbers = private_key.public_key().public_numbers()
        signing_input = b"header.payload"
        signature = private_key.sign(
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        jwks = {
            "keys": [
                {
                    "kid": "key-id",
                    "kty": "RSA",
                    "e": self._encode_int(public_numbers.e),
                    "n": self._encode_int(public_numbers.n),
                }
            ]
        }

        self.provider._verify_signature(
            {"alg": "RS256", "kid": "key-id"},
            signing_input,
            signature,
            jwks,
        )
        with self.assertRaises(OidcTokenValidationError):
            self.provider._verify_signature(
                {"alg": "RS256", "kid": "key-id"},
                signing_input + b"tampered",
                signature,
                jwks,
            )

    @staticmethod
    def _encode_int(value: int) -> str:
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
