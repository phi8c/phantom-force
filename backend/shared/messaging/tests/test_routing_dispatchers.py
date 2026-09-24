from __future__ import annotations

import unittest
from uuid import UUID

from shared.messaging.composition import (
    IngestDispatchers,
    MessagingProviderRegistry,
    UnsupportedQueueProviderError,
)
from shared.messaging.routing import create_routing_dispatchers


RABBIT_JOB = UUID("11111111-1111-1111-1111-111111111111")
AZURE_JOB = UUID("22222222-2222-2222-2222-222222222222")


class FakeRoutingResolver:
    def __init__(self, routes: dict[UUID, str]) -> None:
        self.routes = routes
        self.calls = []

    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        self.calls.append(ingestion_job_id)
        return self.routes[ingestion_job_id]


class RecordingDispatcher:
    def __init__(self, provider: str, stage: str) -> None:
        self.provider = provider
        self.stage = stage
        self.calls = []

    async def dispatch(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))

    async def dispatch_job(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))


def provider_dispatchers(provider: str) -> IngestDispatchers:
    return IngestDispatchers(
        discovery=RecordingDispatcher(provider, "discovery"),
        download=RecordingDispatcher(provider, "download"),
        extraction=RecordingDispatcher(provider, "extraction"),
        chunking=RecordingDispatcher(provider, "chunking"),
        embedding=RecordingDispatcher(provider, "embedding"),
        classification=RecordingDispatcher(provider, "classification"),
    )


class MessagingProviderRegistryTests(unittest.TestCase):
    def test_normalizes_provider_codes(self) -> None:
        rabbit = provider_dispatchers("rabbitmq")
        registry = MessagingProviderRegistry({" RabbitMQ ": rabbit})

        self.assertIs(registry.get("RABBITMQ"), rabbit)

    def test_rejects_duplicate_normalized_codes(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            MessagingProviderRegistry(
                {
                    "rabbitmq": provider_dispatchers("first"),
                    " RABBITMQ ": provider_dispatchers("second"),
                }
            )

    def test_rejects_unsupported_provider(self) -> None:
        registry = MessagingProviderRegistry(
            {"rabbitmq": provider_dispatchers("rabbitmq")}
        )

        with self.assertRaisesRegex(
            UnsupportedQueueProviderError,
            "Unsupported queue provider 'azure_service_bus'",
        ):
            registry.get("azure_service_bus")


class RoutingDispatcherTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.rabbit = provider_dispatchers("rabbitmq")
        self.azure = provider_dispatchers("azure_service_bus")
        self.resolver = FakeRoutingResolver(
            {
                RABBIT_JOB: "rabbitmq",
                AZURE_JOB: "azure_service_bus",
            }
        )
        self.routing = create_routing_dispatchers(
            self.resolver,
            MessagingProviderRegistry(
                {
                    "rabbitmq": self.rabbit,
                    "azure_service_bus": self.azure,
                }
            ),
        )

    async def test_two_jobs_route_to_different_providers(self) -> None:
        await self.routing.discovery.dispatch(RABBIT_JOB, 25)
        await self.routing.discovery.dispatch(AZURE_JOB, 50)

        self.assertEqual(
            self.rabbit.discovery.calls,
            [((RABBIT_JOB, 25), {})],
        )
        self.assertEqual(
            self.azure.discovery.calls,
            [((AZURE_JOB, 50), {})],
        )

    async def test_all_stages_route_through_selected_provider(self) -> None:
        await self.routing.discovery.dispatch(RABBIT_JOB, 20)
        await self.routing.download.dispatch(RABBIT_JOB)
        await self.routing.extraction.dispatch(RABBIT_JOB)
        await self.routing.chunking.dispatch(RABBIT_JOB)
        await self.routing.embedding.dispatch_job(RABBIT_JOB)
        await self.routing.classification.dispatch_job(RABBIT_JOB)

        for dispatcher in (
            self.rabbit.discovery,
            self.rabbit.download,
            self.rabbit.extraction,
            self.rabbit.chunking,
            self.rabbit.embedding,
            self.rabbit.classification,
        ):
            self.assertEqual(len(dispatcher.calls), 1)

        for dispatcher in (
            self.azure.discovery,
            self.azure.download,
            self.azure.extraction,
            self.azure.chunking,
            self.azure.embedding,
            self.azure.classification,
        ):
            self.assertEqual(dispatcher.calls, [])

    async def test_each_transition_resolves_by_ingestion_job(self) -> None:
        await self.routing.download.dispatch(RABBIT_JOB)
        await self.routing.extraction.dispatch(AZURE_JOB)

        self.assertEqual(
            self.resolver.calls,
            [RABBIT_JOB, AZURE_JOB],
        )


if __name__ == "__main__":
    unittest.main()
