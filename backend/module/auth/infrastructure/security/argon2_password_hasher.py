from __future__ import annotations

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError
from argon2.exceptions import InvalidHash

from module.auth.domain.contracts.password_hasher import (
    PasswordHasher,
)


class Argon2idPasswordHasher(
    PasswordHasher,
):
    """
    argon2-cffi mac dinh dung Argon2id (khuyen nghi hien tai cho password
    hashing, uu tien hon bcrypt/PBKDF2). Can: pip install argon2-cffi.
    """

    def __init__(
        self,
    ):
        self._hasher = Argon2Hasher()

    @property
    def algorithm_name(
        self,
    ) -> str:

        return "argon2id"

    def hash(
        self,
        plain_password: str,
    ) -> str:

        return self._hasher.hash(
            plain_password,
        )

    def verify(
        self,
        plain_password: str,
        password_hash: str,
    ) -> bool:

        try:
            return self._hasher.verify(
                password_hash,
                plain_password,
            )
        except (VerifyMismatchError, InvalidHash):
            return False