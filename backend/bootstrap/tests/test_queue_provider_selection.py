from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from bootstrap.queues import create_ingest_messaging


class QueueProviderSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_selects_azure_service_bus(self) -> None:
        expected = object()
        with (
            patch(
                "bootstrap.queues._create_azure_messaging",
                new=AsyncMock(return_value=expected),
            ) as azure,
            patch(
                "bootstrap.queues._create_rabbitmq_messaging",
                new=AsyncMock(),
            ) as rabbitmq,
        ):
            result = await create_ingest_messaging("azure_service_bus")

        self.assertIs(result, expected)
        azure.assert_awaited_once_with()
        rabbitmq.assert_not_awaited()

    async def test_selects_rabbitmq_case_insensitively(self) -> None:
        expected = object()
        with (
            patch(
                "bootstrap.queues._create_azure_messaging",
                new=AsyncMock(),
            ) as azure,
            patch(
                "bootstrap.queues._create_rabbitmq_messaging",
                new=AsyncMock(return_value=expected),
            ) as rabbitmq,
        ):
            result = await create_ingest_messaging(" RabbitMQ ")

        self.assertIs(result, expected)
        azure.assert_not_awaited()
        rabbitmq.assert_awaited_once_with()

    async def test_uses_configured_provider_when_not_explicit(self) -> None:
        expected = object()
        with (
            patch(
                "bootstrap.queues._configured_provider",
                return_value="rabbitmq",
            ),
            patch(
                "bootstrap.queues._create_rabbitmq_messaging",
                new=AsyncMock(return_value=expected),
            ) as rabbitmq,
        ):
            result = await create_ingest_messaging()

        self.assertIs(result, expected)
        rabbitmq.assert_awaited_once_with()

    async def test_rejects_unknown_provider(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "Unsupported QUEUE_PROVIDER 'kafka'",
        ):
            await create_ingest_messaging("kafka")


if __name__ == "__main__":
    unittest.main()
