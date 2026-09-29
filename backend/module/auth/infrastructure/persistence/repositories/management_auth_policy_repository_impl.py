from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.management_auth_policy_repository import (
    ManagementAuthPolicyRepository,
)
from module.auth.domain.entities.management_auth_policy import ManagementAuthPolicy
from module.auth.infrastructure.persistence.mappers.management_auth_policy_mapper import (
    ManagementAuthPolicyMapper,
)
from module.auth.infrastructure.persistence.models.management_auth_policy_model import (
    ManagementAuthPolicyModel,
)
from shared.repositories.base_repository import BaseRepository


class ManagementAuthPolicyRepositoryImpl(
    BaseRepository[ManagementAuthPolicyModel],
    ManagementAuthPolicyRepository,
):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ManagementAuthPolicyModel)

    async def get_active(self) -> ManagementAuthPolicy | None:
        result = await self.session.execute(
            select(ManagementAuthPolicyModel).where(
                ManagementAuthPolicyModel.is_active.is_(True)
            )
        )
        model = result.scalar_one_or_none()
        return ManagementAuthPolicyMapper.to_domain(model) if model else None

    async def get_by_id(self, policy_id: UUID) -> ManagementAuthPolicy | None:
        model = await super().get_by_id(policy_id)
        return ManagementAuthPolicyMapper.to_domain(model) if model else None

    async def add(self, policy: ManagementAuthPolicy) -> ManagementAuthPolicy:
        model = await super().add(ManagementAuthPolicyMapper.to_model(policy))
        return ManagementAuthPolicyMapper.to_domain(model)

    async def update(self, policy: ManagementAuthPolicy) -> None:
        model = await super().get_by_id(policy.id)
        if model is None:
            raise ValueError("Management authentication policy not found")
        ManagementAuthPolicyMapper.merge_into_model(model, policy)
        await self.session.flush()
