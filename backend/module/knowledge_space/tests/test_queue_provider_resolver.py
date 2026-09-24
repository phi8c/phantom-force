from __future__ import annotations

import unittest
from uuid import uuid4

from module.knowledge_space.application.services.queue_provider_resolver import (
    KnowledgeSpaceQueueProviderResolver,
    QueueProviderConfigurationError,
)
from module.knowledge_space.domain.entities.knowledge_space_queue import (
    KnowledgeSpaceQueue,
)
from module.knowledge_space.domain.entities.queue_provider import QueueProvider


class FakeQueueRepository:
    def __init__(self, mapping: KnowledgeSpaceQueue | None) -> None:
        self.mapping = mapping
        self.requested_ids = []

    async def get_default_for_knowledge_space(self, knowledge_space_id):
        self.requested_ids.append(knowledge_space_id)
        return self.mapping


def queue_mapping(
    *,
    mapping_enabled: bool = True,
    provider_enabled: bool = True,
    provider_code: str = "rabbitmq",
    include_provider: bool = True,
) -> KnowledgeSpaceQueue:
    provider = (
        QueueProvider(
            id=uuid4(),
            code=provider_code,
            name="Provider",
            description=None,
            enabled=provider_enabled,
            created_at=None,
            updated_at=None,
        )
        if include_provider
        else None
    )
    return KnowledgeSpaceQueue(
        id=uuid4(),
        knowledge_space_id=uuid4(),
        queue_provider_id=uuid4(),
        configuration={"ignored": True},
        is_default=True,
        enabled=mapping_enabled,
        created_at=None,
        updated_at=None,
        provider=provider,
    )


class QueueProviderResolverTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_normalized_database_provider(self) -> None:
        repository = FakeQueueRepository(
            queue_mapping(provider_code=" RabbitMQ ")
        )
        resolver = KnowledgeSpaceQueueProviderResolver(
            repository,
            fallback_provider_code="azure_service_bus",
        )
        knowledge_space_id = uuid4()

        provider = await resolver.resolve(knowledge_space_id)

        self.assertEqual(provider, "rabbitmq")
        self.assertEqual(repository.requested_ids, [knowledge_space_id])

    async def test_missing_mapping_uses_existing_fallback(self) -> None:
        resolver = KnowledgeSpaceQueueProviderResolver(
            FakeQueueRepository(None),
            fallback_provider_code=" Azure_Service_Bus ",
        )

        self.assertEqual(
            await resolver.resolve(uuid4()),
            "azure_service_bus",
        )

    async def test_disabled_mapping_does_not_fallback(self) -> None:
        resolver = KnowledgeSpaceQueueProviderResolver(
            FakeQueueRepository(queue_mapping(mapping_enabled=False)),
            fallback_provider_code="azure_service_bus",
        )

        with self.assertRaisesRegex(
            QueueProviderConfigurationError,
            "mapping is disabled",
        ):
            await resolver.resolve(uuid4())

    async def test_missing_provider_does_not_fallback(self) -> None:
        resolver = KnowledgeSpaceQueueProviderResolver(
            FakeQueueRepository(queue_mapping(include_provider=False)),
            fallback_provider_code="azure_service_bus",
        )

        with self.assertRaisesRegex(
            QueueProviderConfigurationError,
            "provider does not exist",
        ):
            await resolver.resolve(uuid4())

    async def test_disabled_provider_does_not_fallback(self) -> None:
        resolver = KnowledgeSpaceQueueProviderResolver(
            FakeQueueRepository(queue_mapping(provider_enabled=False)),
            fallback_provider_code="azure_service_bus",
        )

        with self.assertRaisesRegex(
            QueueProviderConfigurationError,
            "provider 'rabbitmq' is disabled",
        ):
            await resolver.resolve(uuid4())

    async def test_empty_provider_code_is_invalid(self) -> None:
        resolver = KnowledgeSpaceQueueProviderResolver(
            FakeQueueRepository(queue_mapping(provider_code=" ")),
            fallback_provider_code="azure_service_bus",
        )

        with self.assertRaisesRegex(
            QueueProviderConfigurationError,
            "queue provider code must not be empty",
        ):
            await resolver.resolve(uuid4())


if __name__ == "__main__":
    unittest.main()
