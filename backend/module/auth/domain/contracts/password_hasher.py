from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class PasswordHasher(
    ABC,
):

    @property
    @abstractmethod
    def algorithm_name(
        self,
    ) -> str:
        """
        Impl tra ve dinh danh thuat toan minh dang dung (vd "argon2id").
        Use case luon hoi qua day, khong bao gio tu hardcode string thuat
        toan - doi implementation khong lam vo use case.
        """
        pass

    @abstractmethod
    def hash(
        self,
        plain_password: str,
    ) -> str:
        pass

    @abstractmethod
    def verify(
        self,
        plain_password: str,
        password_hash: str,
    ) -> bool:
        pass