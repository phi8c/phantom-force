from __future__ import annotations

import hashlib
import secrets

from module.auth.domain.contracts.token_service import (
    TokenService,
)

RAW_TOKEN_BYTES = 32


class SecureTokenService(
    TokenService,
):
    """
    Raw token: secrets.token_urlsafe (CSPRNG, du entropy - 256 bit - khong
    can hash thuat toan "cham" nhu Argon2 vi day khong phai secret do nguoi
    dat, ma la random string). Hash: SHA-256 - du nhanh, du an toan cho
    muc dich chi de so khop, khong phai chong brute-force tu 1 gia tri
    thap-entropy nhu password.
    """

    def generate_raw_token(
        self,
    ) -> str:

        return secrets.token_urlsafe(
            RAW_TOKEN_BYTES,
        )

    def hash(
        self,
        raw_token: str,
    ) -> str:

        return hashlib.sha256(
            raw_token.encode(
                "utf-8",
            ),
        ).hexdigest()