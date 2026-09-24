from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Mapping, Sequence

from shared.messaging.contracts import MessageConsumer, ReceivedMessage

from .models import IngestConsumers


class CompositeConsumerError(RuntimeError):
    pass


class CompositeMessageConsumer(MessageConsumer):
    def __init__(
        self,
        consumers: Mapping[str, MessageConsumer],
    ) -> None:
        if not consumers:
            raise ValueError("At least one provider consumer is required.")
        self._consumers = tuple(consumers.items())
        self._pending: deque[ReceivedMessage] = deque()

    async def receive(
        self,
        *,
        max_messages: int = 1,
        wait_timeout: float = 5,
    ) -> list[ReceivedMessage]:
        if max_messages <= 0:
            raise ValueError("max_messages must be greater than 0.")
        if wait_timeout < 0:
            raise ValueError("wait_timeout cannot be negative.")

        buffered = self._drain_pending(max_messages)
        if len(buffered) >= max_messages:
            return buffered

        tasks = {
            asyncio.create_task(
                consumer.receive(
                    max_messages=max_messages,
                    wait_timeout=wait_timeout,
                )
            ): provider_code
            for provider_code, consumer in self._consumers
        }
        failures: list[tuple[str, BaseException]] = []
        successful_provider_count = 0

        try:
            while tasks:
                done, _ = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                completed_messages: list[ReceivedMessage] = []
                for task in done:
                    provider_code = tasks.pop(task)
                    try:
                        messages = task.result()
                    except Exception as exc:
                        failures.append((provider_code, exc))
                    else:
                        successful_provider_count += 1
                        completed_messages.extend(messages)

                if completed_messages:
                    self._pending.extend(completed_messages)
                    (
                        raced_messages,
                        raced_failures,
                        raced_success_count,
                    ) = await self._cancel_and_collect(tasks)
                    self._pending.extend(raced_messages)
                    failures.extend(raced_failures)
                    successful_provider_count += raced_success_count
                    tasks.clear()
                    break
        finally:
            await self._cancel_tasks(tasks)

        buffered.extend(
            self._drain_pending(max_messages - len(buffered))
        )
        if buffered or successful_provider_count:
            return buffered
        details = ", ".join(
            f"{provider}: {type(error).__name__}"
            for provider, error in failures
        )
        raise CompositeConsumerError(
            f"All messaging providers failed to receive ({details})."
        ) from failures[0][1]

    def _drain_pending(self, limit: int) -> list[ReceivedMessage]:
        messages = []
        while self._pending and len(messages) < limit:
            messages.append(self._pending.popleft())
        return messages

    @staticmethod
    async def _cancel_and_collect(
        tasks: Mapping[asyncio.Task, str],
    ) -> tuple[
        list[ReceivedMessage],
        list[tuple[str, BaseException]],
        int,
    ]:
        messages: list[ReceivedMessage] = []
        failures: list[tuple[str, BaseException]] = []
        successful_provider_count = 0
        task_items = list(tasks.items())
        for task, _ in task_items:
            if not task.done():
                task.cancel()
        if task_items:
            await asyncio.gather(
                *(task for task, _ in task_items),
                return_exceptions=True,
            )
        for task, provider_code in task_items:
            if task.cancelled():
                continue
            try:
                result = task.result()
            except Exception as exc:
                failures.append((provider_code, exc))
            else:
                successful_provider_count += 1
                messages.extend(result)
        return messages, failures, successful_provider_count

    @staticmethod
    async def _cancel_tasks(
        tasks: Mapping[asyncio.Task, str] | Sequence[asyncio.Task],
    ) -> None:
        pending_tasks = list(tasks)
        for task in pending_tasks:
            if not task.done():
                task.cancel()
        if pending_tasks:
            await asyncio.gather(
                *pending_tasks,
                return_exceptions=True,
            )


def create_composite_consumers(
    providers: Mapping[str, IngestConsumers],
) -> IngestConsumers:
    if not providers:
        raise ValueError("At least one messaging provider is required.")

    def stage_consumers(stage: str) -> dict[str, MessageConsumer]:
        return {
            provider_code: getattr(consumers, stage)
            for provider_code, consumers in providers.items()
        }

    return IngestConsumers(
        discovery=CompositeMessageConsumer(
            stage_consumers("discovery")
        ),
        download=CompositeMessageConsumer(
            stage_consumers("download")
        ),
        extraction=CompositeMessageConsumer(
            stage_consumers("extraction")
        ),
        chunking=CompositeMessageConsumer(
            stage_consumers("chunking")
        ),
        embedding=CompositeMessageConsumer(
            stage_consumers("embedding")
        ),
        classification=CompositeMessageConsumer(
            stage_consumers("classification")
        ),
    )
