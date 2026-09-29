import base64
import hashlib
import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes

from module.auth.domain.contracts.oidc_provider import OidcProvider
from module.auth.domain.exception.exceptions import (
    OidcTenantMismatchError,
    OidcTokenValidationError,
)
from module.auth.domain.value_objects.oidc_user_info import OidcUserInfo


class MicrosoftEntraOidcProvider(OidcProvider):
    def __init__(
        self,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str | None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._http_client = http_client

    def build_authorization_url(
        self,
        expected_tenant_id: str,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        self._require_configuration()
        query = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_uri": self._redirect_uri,
                "response_mode": "query",
                "scope": "openid profile email",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        return (
            f"https://login.microsoftonline.com/{expected_tenant_id}"
            f"/oauth2/v2.0/authorize?{query}"
        )

    async def exchange_code_and_verify(
        self,
        expected_tenant_id: str,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcUserInfo:
        self._require_configuration()
        discovery_url = (
            f"https://login.microsoftonline.com/{expected_tenant_id}"
            "/v2.0/.well-known/openid-configuration"
        )
        try:
            discovery = await self._get_json(discovery_url)
            token_payload = await self._post_form(
                discovery["token_endpoint"],
                {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                    "code_verifier": code_verifier,
                },
            )
            id_token = token_payload["id_token"]
            header, claims, signing_input, signature = self._decode_jwt(id_token)
            jwks = await self._get_json(discovery["jwks_uri"])
            self._verify_signature(header, signing_input, signature, jwks)
            self._validate_claims(
                claims=claims,
                expected_issuer=discovery["issuer"],
                expected_nonce=expected_nonce,
                expected_tenant_id=expected_tenant_id,
            )
            external_sub = claims.get("oid") or claims.get("sub")
            email = claims.get("email") or claims.get("preferred_username")
            if not isinstance(external_sub, str) or not external_sub:
                raise OidcTokenValidationError("OIDC subject is missing")
            if not isinstance(email, str) or not email:
                raise OidcTokenValidationError("OIDC email is missing")
            return OidcUserInfo(
                external_sub=external_sub,
                email=email,
                email_verified=claims.get("email_verified") is True,
                tenant_id=claims["tid"],
            )
        except (OidcTokenValidationError, OidcTenantMismatchError):
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise OidcTokenValidationError("OIDC token validation failed") from exc

    async def _get_json(self, url: str) -> dict[str, Any]:
        if self._http_client is not None:
            response = await self._http_client.get(url)
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def _post_form(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        if self._http_client is not None:
            response = await self._http_client.post(url, data=data)
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, data=data)
        response.raise_for_status()
        return response.json()

    def _validate_claims(
        self,
        claims: dict[str, Any],
        expected_issuer: str,
        expected_nonce: str,
        expected_tenant_id: str,
    ) -> None:
        now = int(time.time())
        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if claims.get("iss") != expected_issuer:
            raise OidcTokenValidationError("OIDC issuer is invalid")
        if self._client_id not in audiences:
            raise OidcTokenValidationError("OIDC audience is invalid")
        if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] <= now:
            raise OidcTokenValidationError("OIDC token has expired")
        if isinstance(claims.get("nbf"), (int, float)) and claims["nbf"] > now + 60:
            raise OidcTokenValidationError("OIDC token is not active")
        if claims.get("nonce") != expected_nonce:
            raise OidcTokenValidationError("OIDC nonce is invalid")
        if claims.get("tid") != expected_tenant_id:
            raise OidcTenantMismatchError("OIDC tenant is invalid")

    @classmethod
    def _verify_signature(cls, header, signing_input, signature, jwks) -> None:
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise OidcTokenValidationError("OIDC signing algorithm is invalid")
        key = next(
            (item for item in jwks.get("keys", []) if item.get("kid") == header["kid"]),
            None,
        )
        if key is None or key.get("kty") != "RSA":
            raise OidcTokenValidationError("OIDC signing key is unavailable")
        public_key = rsa.RSAPublicNumbers(
            cls._decode_int(key["e"]),
            cls._decode_int(key["n"]),
        ).public_key()
        try:
            public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature as exc:
            raise OidcTokenValidationError("OIDC signature is invalid") from exc

    @classmethod
    def _decode_jwt(cls, token: str):
        parts = token.split(".")
        if len(parts) != 3:
            raise OidcTokenValidationError("OIDC token is malformed")
        header = json.loads(cls._decode_bytes(parts[0]))
        claims = json.loads(cls._decode_bytes(parts[1]))
        return (
            header,
            claims,
            f"{parts[0]}.{parts[1]}".encode("ascii"),
            cls._decode_bytes(parts[2]),
        )

    @staticmethod
    def _decode_bytes(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    @classmethod
    def _decode_int(cls, value: str) -> int:
        return int.from_bytes(cls._decode_bytes(value), "big")

    def _require_configuration(self) -> None:
        if not self._client_id or not self._client_secret or not self._redirect_uri:
            raise RuntimeError("Microsoft Entra OIDC is not configured")
