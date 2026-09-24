from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock
from uuid import UUID

from shared.messaging.composition import (
    IngestDispatchers,
    IngestProducer,
    LazyMessagingProviderRegistry,
)
from shared.messaging.routing import create_routing_dispatchers


RABBIT_JOB = UUID("11111111-1111-1111-1111-111111111111")
AZURE_JOB = UUID("22222222-2222-2222-2222-222222222222")


class FakeResolver:
    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        if ingestion_job_id == RABBIT_JOB:
            return "rabbitmq"
        return "azure_service_bus"


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls = []

    async def dispatch(self, *args) -> None:
        self.calls.append(args)

    async def dispatch_job(self, *args) -> None:
        self.calls.append(args)


def producer(close: AsyncMock) -> tuple[IngestProducer, RecordingDispatcher]:
    dispatcher = RecordingDispatcher()
    dispatchers = IngestDispatchers(
        discovery=dispatcher,
        download=dispatcher,
        extraction=dispatcher,
        chunking=dispatcher,
        embedding=dispatcher,
        classification=dispatcher,
    )
    return IngestProducer(dispatchers, close), dispatcher


class LazyMessagingProviderRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_routes_only_to_selected_rabbitmq_provider(self) -> None:
        rabbit_close = AsyncMock()
        rabbit, dispatcher = producer(rabbit_close)
        rabbit_factory = AsyncMock(return_value=rabbit)
        azure_factory = AsyncMock(side_effect=RuntimeError("azure down"))
        registry = LazyMessagingProviderRegistry(
            {"rabbitmq": rabbit_factory, "azure_service_bus": azure_factory}
        )
        routing = create_routing_dispatchers(FakeResolver(), registry)

        await routing.discovery.dispatch(RABBIT_JOB, 25)

        rabbit_factory.assert_awaited_once_with()
        azure_factory.assert_not_awaited()
        self.assertEqual(dispatcher.calls, [(RABBIT_JOB, 25)])

    async def test_routes_only_to_selected_azure_provider(self) -> None:
        azure_close = AsyncMock()
        azure, dispatcher = producer(azure_close)
        azure_factory = AsyncMock(return_value=azure)
        rabbit_factory = AsyncMock(side_effect=RuntimeError("rabbit down"))
        registry = LazyMessagingProviderRegistry(
            {"rabbitmq": rabbit_factory, "azure_service_bus": azure_factory}
        )
        routing = create_routing_dispatchers(FakeResolver(), registry)

        await routing.discovery.dispatch(AZURE_JOB, 50)

        azure_factory.assert_awaited_once_with()
        rabbit_factory.assert_not_awaited()
        self.assertEqual(dispatcher.calls, [(AZURE_JOB, 50)])

    async def test_reuses_provider_across_dispatches(self) -> None:
        resource, _ = producer(AsyncMock())
        factory = AsyncMock(return_value=resource)
        registry = LazyMessagingProviderRegistry({"rabbitmq": factory})

        first = await registry.get("rabbitmq")
        second = await registry.get(" RABBITMQ ")

        self.assertIs(first, second)
        factory.assert_awaited_once_with()

    async def test_concurrent_get_initializes_provider_once(self) -> None:
        resource, _ = producer(AsyncMock())
        calls = 0

        async def factory():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.01)
            return resource

        registry = LazyMessagingProviderRegistry({"rabbitmq": factory})
        providers = await asyncio.gather(
            *(registry.get("rabbitmq") for _ in range(10))
        )

        self.assertTrue(all(item is providers[0] for item in providers))
        self.assertEqual(calls, 1)

    async def test_close_only_closes_initialized_provider_once(self) -> None:
        rabbit_close = AsyncMock()
        azure_close = AsyncMock()
        rabbit, _ = producer(rabbit_close)
        azure, _ = producer(azure_close)
        rabbit_factory = AsyncMock(return_value=rabbit)
        azure_factory = AsyncMock(return_value=azure)
        registry = LazyMessagingProviderRegistry(
            {"rabbitmq": rabbit_factory, "azure_service_bus": azure_factory}
        )

        await registry.get("rabbitmq")
        await registry.close()
        await registry.close()

        rabbit_close.assert_awaited_once_with()
        azure_close.assert_not_awaited()
        azure_factory.assert_not_awaited()

    async def test_close_without_dispatch_does_not_initialize_provider(self) -> None:
        factory = AsyncMock()
        registry = LazyMessagingProviderRegistry({"rabbitmq": factory})

        await registry.close()
        await registry.close()

        factory.assert_not_awaited()

    async def test_failed_factory_is_not_cached_or_shared_with_other_provider(
        self,
    ) -> None:
        rabbit, _ = producer(AsyncMock())
        azure, _ = producer(AsyncMock())
        rabbit_factory = AsyncMock(
            side_effect=[RuntimeError("rabbit down"), rabbit]
        )
        azure_factory = AsyncMock(return_value=azure)
        registry = LazyMessagingProviderRegistry(
            {"rabbitmq": rabbit_factory, "azure_service_bus": azure_factory}
        )

        with self.assertRaisesRegex(RuntimeError, "rabbit down"):
            await registry.get("rabbitmq")

        self.assertIs(
            await registry.get("azure_service_bus"),
            azure.dispatchers,
        )
        self.assertIs(await registry.get("rabbitmq"), rabbit.dispatchers)
        self.assertEqual(rabbit_factory.await_count, 2)
        azure_factory.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
