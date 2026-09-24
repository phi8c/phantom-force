from __future__ import annotations

import unittest
from contextlib import asynccontextmanager
from uuid import UUID

from shared.messaging.routing import ScopedQueueRoutingResolver


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")


class FakeResolver:
    def __init__(self) -> None:
        self.job_ids = []

    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        self.job_ids.append(ingestion_job_id)
        return "azure_service_bus"


class ScopedQueueRoutingResolverTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_opens_and_closes_scope_for_each_resolution(self) -> None:
        events = []
        resolver = FakeResolver()

        @asynccontextmanager
        async def scope():
            events.append("open")
            try:
                yield resolver
            finally:
                events.append("close")

        scoped = ScopedQueueRoutingResolver(scope)

        first = await scoped.resolve_for_job(JOB_ID)
        second = await scoped.resolve_for_job(JOB_ID)

        self.assertEqual(first, "azure_service_bus")
        self.assertEqual(second, "azure_service_bus")
        self.assertEqual(resolver.job_ids, [JOB_ID, JOB_ID])
        self.assertEqual(
            events,
            ["open", "close", "open", "close"],
        )


if __name__ == "__main__":
    unittest.main()
