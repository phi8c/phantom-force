from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.knowledge_space_auth_policy_repository import (
    KnowledgeSpaceAuthPolicyRepository,
)
from module.auth.domain.entities.knowledge_space_auth_policy import (
    KnowledgeSpaceAuthPolicy,
)
from module.auth.infrastructure.persistence.mappers.knowledge_space_auth_policy_mapper import (
    KnowledgeSpaceAuthPolicyMapper,
)
from module.auth.infrastructure.persistence.models.knowledge_space_auth_policy_model import (
    KnowledgeSpaceAuthPolicyModel,
)
from shared.repositories.base_repository import BaseRepository


class KnowledgeSpaceAuthPolicyRepositoryImpl(
    BaseRepository[KnowledgeSpaceAuthPolicyModel],
    KnowledgeSpaceAuthPolicyRepository,
):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=KnowledgeSpaceAuthPolicyModel)

    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceAuthPolicy | None:
        result = await self.session.execute(
            select(KnowledgeSpaceAuthPolicyModel).where(
                KnowledgeSpaceAuthPolicyModel.knowledge_space_id
                == knowledge_space_id
            )
        )
        model = result.scalar_one_or_none()
        return (
            KnowledgeSpaceAuthPolicyMapper.to_domain(model)
            if model is not None
            else None
        )

    async def add(
        self,
        policy: KnowledgeSpaceAuthPolicy,
    ) -> KnowledgeSpaceAuthPolicy:
        model = await super().add(KnowledgeSpaceAuthPolicyMapper.to_model(policy))
        return KnowledgeSpaceAuthPolicyMapper.to_domain(model)

    async def update(self, policy: KnowledgeSpaceAuthPolicy) -> None:
        model = await super().get_by_id(policy.id)
        if model is None:
            raise ValueError("Knowledge Space authentication policy not found")
        KnowledgeSpaceAuthPolicyMapper.merge_into_model(model, policy)
        await self.session.flush()
