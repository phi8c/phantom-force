from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from ..entities.credential import Credential
from ..entities.mfa_recovery_code import MfaRecoveryCode
from ..entities.password_history import PasswordHistory


class CredentialRepository(
    ABC,
):

    # --- credentials ---

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Credential | None:
        pass

    @abstractmethod
    async def add(
        self,
        entity: Credential,
    ) -> Credential:
        pass

    @abstractmethod
    async def update(
        self,
        entity: Credential,
    ) -> None:
        pass

    # --- password_history ---

    @abstractmethod
    async def add_password_history(
        self,
        entity: PasswordHistory,
    ) -> PasswordHistory:
        pass

    @abstractmethod
    async def list_recent_password_hashes(
        self,
        user_id: UUID,
        limit: int,
    ) -> list[str]:
        pass

    # --- mfa_recovery_codes ---

    @abstractmethod
    async def add_recovery_codes(
        self,
        entities: list[MfaRecoveryCode],
    ) -> None:
        pass

    @abstractmethod
    async def get_unused_recovery_codes(
        self,
        user_id: UUID,
    ) -> list[MfaRecoveryCode]:
        pass

    @abstractmethod
    async def mark_recovery_code_used(
        self,
        code_id: UUID,
        used_at: datetime,
    ) -> None:
        pass

    @abstractmethod
    async def delete_all_recovery_codes(
        self,
        user_id: UUID,
    ) -> None:
        pass