from module.knowledge_space.domain.entities.knowledge_space_queue import (
    KnowledgeSpaceQueue,
)
from module.knowledge_space.domain.entities.queue_provider import QueueProvider
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_queue_model import (
    KnowledgeSpaceQueueModel,
)
from module.knowledge_space.infrastructure.persistence.models.queue_provider_model import (
    QueueProviderModel,
)


class KnowledgeSpaceQueueMapper:
    @staticmethod
    def to_entity(
        mapping: KnowledgeSpaceQueueModel,
        provider: QueueProviderModel | None,
    ) -> KnowledgeSpaceQueue:
        provider_entity = None
        if provider is not None:
            provider_entity = QueueProvider(
                id=provider.id,
                code=provider.code,
                name=provider.name,
                description=provider.description,
                enabled=provider.enabled,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
            )
        return KnowledgeSpaceQueue(
            id=mapping.id,
            knowledge_space_id=mapping.knowledge_space_id,
            queue_provider_id=mapping.queue_provider_id,
            configuration=dict(mapping.configuration or {}),
            is_default=mapping.is_default,
            enabled=mapping.enabled,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
            provider=provider_entity,
        )
