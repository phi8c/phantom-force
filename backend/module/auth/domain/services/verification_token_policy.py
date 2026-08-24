from __future__ import annotations

from datetime import timedelta

from ..enums.token_purpose import TokenPurpose

_TTL_BY_PURPOSE: dict[TokenPurpose, timedelta] = {
    TokenPurpose.EMAIL_VERIFY: timedelta(minutes=30),
    TokenPurpose.PASSWORD_RESET: timedelta(minutes=15),
}


class VerificationTokenPolicy:
    """
    TTL khac nhau theo tung purpose - tap trung 1 cho tren rule nay, khong
    de moi use case tu khai magic constant rieng le nhu truoc.
    """

    def ttl_for(
        self,
        purpose: TokenPurpose,
    ) -> timedelta:

        ttl = _TTL_BY_PURPOSE.get(
            purpose,
        )

        if ttl is None:
            raise ValueError(
                f"Khong co TTL policy cho purpose: {purpose}",
            )

        return ttl