from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class TokenService(
    ABC,
):
    """
    Sinh raw token ngau nhien (session/refresh/verification token) va hash no.
    Raw token CHI duoc dung 1 lan de tra ve client (cookie/link email), khong
    bao gio persist - chi persist ban hash tra ve tu hash().
    """

    @abstractmethod
    def generate_raw_token(
        self,
    ) -> str:
        pass

    @abstractmethod
    def hash(
        self,
        raw_token: str,
    ) -> str:
        pass