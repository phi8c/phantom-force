from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class Encryptor(
    ABC,
):
    """
    Envelope encryption cho du lieu can doc lai duoc (vd mfa_secret_encrypted).
    Impl thuc te goi KMS/Vault - domain khong biet chi tiet ha tang nao dung.
    """

    @abstractmethod
    async def encrypt(
        self,
        plaintext: str,
    ) -> str:
        pass

    @abstractmethod
    async def decrypt(
        self,
        ciphertext: str,
    ) -> str:
        pass