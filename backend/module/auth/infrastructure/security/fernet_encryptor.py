from cryptography.fernet import Fernet, InvalidToken

from module.auth.domain.contracts.encryptor import Encryptor


class FernetEncryptor(Encryptor):
    def __init__(self, key: str | None):
        self._fernet = Fernet(key.encode("ascii")) if key else None

    async def encrypt(self, plaintext: str) -> str:
        if self._fernet is None:
            raise RuntimeError("MFA encryption key has not been configured")
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    async def decrypt(self, ciphertext: str) -> str:
        if self._fernet is None:
            raise RuntimeError("MFA encryption key has not been configured")
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Encrypted MFA secret is invalid") from exc
