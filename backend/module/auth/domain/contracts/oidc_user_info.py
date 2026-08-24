from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OidcUserInfo:
    """
    Ket qua sau khi verify id_token (chu ky, iss, aud, nonce). Chi giu lai
    thong tin can thiet - id_token/access_token/refresh_token cua IdP KHONG
    duoc dua vao value object nay, discard ngay sau buoc verify.
    """

    external_sub: str

    email: str

    email_verified: bool

    tenant_id: str | None

    roles: list[str]