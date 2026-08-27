from __future__ import annotations

from datetime import datetime
from uuid import UUID
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.credential_repository import (
    CredentialRepository,
)
from module.auth.domain.entities.credential import (
    Credential,
)
from module.auth.domain.entities.mfa_recovery_code import (
    MfaRecoveryCode,
)
from module.auth.domain.entities.password_history import (
    PasswordHistory,
)

from module.auth.infrastructure.persistence.mappers.credential_mapper import (
    CredentialMapper,
)
from module.auth.infrastructure.persistence.mappers.mfa_recovery_code_mapper import (
    MfaRecoveryCodeMapper,
)
from module.auth.infrastructure.persistence.mappers.password_history_mapper import (
    PasswordHistoryMapper,
)
from module.auth.infrastructure.persistence.models.credential_model import (
    CredentialModel,
)
from module.auth.infrastructure.persistence.models.mfa_recovery_code_model import (
    MfaRecoveryCodeModel,
)
from module.auth.infrastructure.persistence.models.password_history_model import (
    PasswordHistoryModel,
)

from shared.repositories.base_repository import (
    BaseRepository,
)


class CredentialRepositoryImpl(
    BaseRepository[CredentialModel],
    CredentialRepository,
):
    """
    PK cua CredentialModel la user_id (khong phai id), nen KHONG dung
    BaseRepository.get_by_id()/exists() cho Credential - 2 ham do hardcode
    cot `.id`. Chi tai su dung add()/delete() vi 2 ham nay khong phu thuoc
    ten cot PK.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=CredentialModel,
        )

    # --- credentials ---

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Credential | None:

        result = await self.session.execute(
            select(
                CredentialModel,
            ).where(
                CredentialModel.user_id == user_id,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return CredentialMapper.to_domain(
            model,
        )

    async def add(
        self,
        entity: Credential,
    ) -> Credential:

        model = CredentialMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return CredentialMapper.to_domain(
            model,
        )

    async def update(
        self,
        entity: Credential,
    ) -> None:

        result = await self.session.execute(
            select(
                CredentialModel,
            ).where(
                CredentialModel.user_id == entity.user_id,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(
                "Credential not found",
            )

        CredentialMapper.merge_into_model(
            model,
            entity,
        )

        await self.session.flush()

    # --- password_history ---

    async def add_password_history(
        self,
        entity: PasswordHistory,
    ) -> PasswordHistory:

        model = PasswordHistoryMapper.to_model(
            entity,
        )

        self.session.add(
            model,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return PasswordHistoryMapper.to_domain(
            model,
        )

    async def list_recent_password_hashes(
        self,
        user_id: UUID,
        limit: int,
    ) -> list[str]:

        result = await self.session.execute(
            select(
                PasswordHistoryModel.password_hash,
            )
            .where(
                PasswordHistoryModel.user_id == user_id,
            )
            .order_by(
                PasswordHistoryModel.created_at.desc(),
            )
            .limit(
                limit,
            ),
        )

        return list(
            result.scalars().all(),
        )

    # --- mfa_recovery_codes ---

    async def add_recovery_codes(
        self,
        entities: list[MfaRecoveryCode],
    ) -> None:

        models = [
            MfaRecoveryCodeMapper.to_model(
                entity,
            )
            for entity in entities
        ]

        self.session.add_all(
            models,
        )

        await self.session.flush()

    async def get_unused_recovery_codes(
        self,
        user_id: UUID,
    ) -> list[MfaRecoveryCode]:

        result = await self.session.execute(
            select(
                MfaRecoveryCodeModel,
            ).where(
                MfaRecoveryCodeModel.user_id == user_id,
                MfaRecoveryCodeModel.used_at.is_(
                    None,
                ),
            ),
        )

        return [
            MfaRecoveryCodeMapper.to_domain(
                model,
            )
            for model in result.scalars().all()
        ]

    async def mark_recovery_code_used(
        self,
        code_id: UUID,
        used_at: datetime,
    ) -> None:

        result = await self.session.execute(
            select(
                MfaRecoveryCodeModel,
            ).where(
                MfaRecoveryCodeModel.id == code_id,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(
                "Recovery code not found",
            )

        model.used_at = used_at

        await self.session.flush()

    async def delete_all_recovery_codes(
        self,
        user_id: UUID,
    ) -> None:

        await self.session.execute(
            delete(
                MfaRecoveryCodeModel,
            ).where(
                MfaRecoveryCodeModel.user_id == user_id,
            ),
        )

        await self.session.flush()