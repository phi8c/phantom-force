from __future__ import annotations

import asyncio
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from workers.ingest.discovery_worker import DiscoveryWorker


class FakeMessage:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.acked = False
        self.nacked = False

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, *, requeue: bool = True) -> None:
        self.nacked = requeue


class OneMessageConsumer:
    def __init__(self, message: FakeMessage) -> None:
        self.message = message
        self.calls = 0

    async def receive(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return [self.message]
        raise asyncio.CancelledError


class FakeUseCase:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.requests = []

    async def execute(self, request):
        self.requests.append(request)
        if self.should_fail:
            raise RuntimeError("processing failed")
        return SimpleNamespace(items=[], has_more=False)


class FakeDispatcher:
    async def dispatch(self, **kwargs) -> None:
        raise AssertionError("Discovery should not redispatch when has_more is false.")


class DiscoveryWorkerMessagingTests(unittest.IsolatedAsyncioTestCase):
    def _worker(self, message: FakeMessage, use_case: FakeUseCase) -> DiscoveryWorker:
        @asynccontextmanager
        async def use_case_factory():
            yield use_case

        return DiscoveryWorker(
            consumer=OneMessageConsumer(message),
            use_case_factory=use_case_factory,
            discovery_dispatcher=FakeDispatcher(),
        )

    async def test_success_acknowledges_after_processing(self) -> None:
        use_case = FakeUseCase()
        message = FakeMessage(
            {
                "ingestion_job_id": str(uuid4()),
                "batch_size": 25,
            }
        )
        worker = self._worker(message, use_case)

        with patch(
            "workers.ingest.discovery_worker.asyncio.sleep",
            new=AsyncMock(),
        ):
            with self.assertRaises(asyncio.CancelledError):
                await worker.run()

        self.assertEqual(len(use_case.requests), 1)
        self.assertTrue(message.acked)
        self.assertFalse(message.nacked)

    async def test_failure_nacks_without_acknowledging(self) -> None:
        use_case = FakeUseCase(should_fail=True)
        message = FakeMessage(
            {
                "ingestion_job_id": str(uuid4()),
                "batch_size": 25,
            }
        )
        worker = self._worker(message, use_case)

        async def nack_without_delay(received, **kwargs) -> None:
            await received.nack(requeue=True)

        with (
            patch(
                "workers.ingest.discovery_worker.asyncio.sleep",
                new=AsyncMock(),
            ),
            patch(
                "workers.ingest.discovery_worker.nack_with_backoff",
                new=nack_without_delay,
            ),
        ):
            with self.assertRaises(asyncio.CancelledError):
                await worker.run()

        self.assertFalse(message.acked)
        self.assertTrue(message.nacked)


if __name__ == "__main__":
    unittest.main()
