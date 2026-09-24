from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from bootstrap.queues import create_ingest_messaging
from shared.messaging.composition import (
    CompositeMessageConsumer,
    IngestConsumers,
    IngestDispatchers,
    IngestMessaging,
)


class FakeConsumer:
    async def receive(self, **kwargs):
        return []


class FakeDispatcher:
    def __init__(self, provider: str) -> None:
        self.provider = provider
        self.calls = []

    async def dispatch(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))

    async def dispatch_job(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))


def provider_bundle(
    provider: str,
    close_callback,
) -> IngestMessaging:
    consumer = FakeConsumer()
    dispatcher = FakeDispatcher(provider)
    return IngestMessaging(
        consumers=IngestConsumers(
            discovery=consumer,
            download=consumer,
            extraction=consumer,
            chunking=consumer,
            embedding=consumer,
            classification=consumer,
        ),
        dispatchers=IngestDispatchers(
            discovery=dispatcher,
            download=dispatcher,
            extraction=dispatcher,
            chunking=dispatcher,
            embedding=dispatcher,
            classification=dispatcher,
        ),
        _close_callback=close_callback,
    )


class MultiProviderMessagingBootstrapTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_starts_both_providers_and_returns_composite_runtime(
        self,
    ) -> None:
        close_azure = AsyncMock()
        close_rabbit = AsyncMock()
        azure_bundle = provider_bundle(
            "azure_service_bus",
            close_azure,
        )
        rabbit_bundle = provider_bundle(
            "rabbitmq",
            close_rabbit,
        )

        with (
            patch(
                "bootstrap.queues._create_azure_messaging",
                new=AsyncMock(return_value=azure_bundle),
            ) as azure,
            patch(
                "bootstrap.queues._create_rabbitmq_messaging",
                new=AsyncMock(return_value=rabbit_bundle),
            ) as rabbitmq,
        ):
            messaging = await create_ingest_messaging()

        azure.assert_awaited_once_with()
        rabbitmq.assert_awaited_once_with()
        self.assertIsInstance(
            messaging.consumers.discovery,
            CompositeMessageConsumer,
        )

        await messaging.close()

        close_rabbit.assert_awaited_once_with()
        close_azure.assert_awaited_once_with()

    async def test_closes_azure_when_rabbitmq_startup_fails(self) -> None:
        close_azure = AsyncMock()
        azure_bundle = provider_bundle(
            "azure_service_bus",
            close_azure,
        )

        with (
            patch(
                "bootstrap.queues._create_azure_messaging",
                new=AsyncMock(return_value=azure_bundle),
            ),
            patch(
                "bootstrap.queues._create_rabbitmq_messaging",
                new=AsyncMock(
                    side_effect=RuntimeError("rabbit startup failed")
                ),
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "rabbit startup failed",
            ):
                await create_ingest_messaging()

        close_azure.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
