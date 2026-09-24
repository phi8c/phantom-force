from __future__ import annotations

import unittest
from types import SimpleNamespace
from uuid import UUID

from module.ingest.config.application.services.queue_routing_resolver import (
    IngestionJobQueueRoutingResolver,
)


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")
KNOWLEDGE_SPACE_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeIngestionRepository:
    def __init__(self, job) -> None:
        self.job = job
        self.requested_job_ids = []

    async def get_job_by_id(self, job_id: UUID):
        self.requested_job_ids.append(job_id)
        return self.job


class FakeQueueProviderResolver:
    def __init__(self, provider_code: str) -> None:
        self.provider_code = provider_code
        self.requested_knowledge_space_ids = []

    async def resolve(self, knowledge_space_id: UUID) -> str:
        self.requested_knowledge_space_ids.append(knowledge_space_id)
        return self.provider_code


class IngestionJobQueueRoutingResolverTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_resolves_job_knowledge_space_provider(self) -> None:
        repository = FakeIngestionRepository(
            SimpleNamespace(knowledge_space_id=KNOWLEDGE_SPACE_ID)
        )
        provider_resolver = FakeQueueProviderResolver("rabbitmq")
        resolver = IngestionJobQueueRoutingResolver(
            repository,
            provider_resolver,
        )

        provider = await resolver.resolve_for_job(JOB_ID)

        self.assertEqual(provider, "rabbitmq")
        self.assertEqual(repository.requested_job_ids, [JOB_ID])
        self.assertEqual(
            provider_resolver.requested_knowledge_space_ids,
            [KNOWLEDGE_SPACE_ID],
        )

    async def test_rejects_missing_ingestion_job(self) -> None:
        provider_resolver = FakeQueueProviderResolver("rabbitmq")
        resolver = IngestionJobQueueRoutingResolver(
            FakeIngestionRepository(None),
            provider_resolver,
        )

        with self.assertRaisesRegex(LookupError, str(JOB_ID)):
            await resolver.resolve_for_job(JOB_ID)

        self.assertEqual(
            provider_resolver.requested_knowledge_space_ids,
            [],
        )


if __name__ == "__main__":
    unittest.main()
