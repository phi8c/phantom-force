import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote, urlencode

from module.auth.domain.contracts.mfa_provider import MfaProvider


class TotpMfaProvider(MfaProvider):
    def __init__(self, issuer: str, period_seconds: int = 30, digits: int = 6):
        self._issuer = issuer
        self._period_seconds = period_seconds
        self._digits = digits

    def generate_secret(self) -> str:
        return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")

    def generate_provisioning_uri(self, secret: str, account_email: str) -> str:
        label = quote(f"{self._issuer}:{account_email}", safe="")
        query = urlencode(
            {
                "secret": secret,
                "issuer": self._issuer,
                "algorithm": "SHA1",
                "digits": self._digits,
                "period": self._period_seconds,
            }
        )
        return f"otpauth://totp/{label}?{query}"

    def verify_totp(self, secret: str, code: str) -> bool:
        if not code.isdigit() or len(code) != self._digits:
            return False
        counter = int(time.time()) // self._period_seconds
        return any(
            hmac.compare_digest(self._code(secret, counter + drift), code)
            for drift in (-1, 0, 1)
        )

    def _code(self, secret: str, counter: int) -> str:
        padded = secret + "=" * (-len(secret) % 8)
        key = base64.b32decode(padded, casefold=True)
        digest = hmac.new(
            key,
            struct.pack(">Q", counter),
            hashlib.sha1,
        ).digest()
        offset = digest[-1] & 0x0F
        value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
        return str(value % (10**self._digits)).zfill(self._digits)
