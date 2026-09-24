from __future__ import annotations

from collections.abc import Callable
from typing import AsyncContextManager
from uuid import UUID

from shared.messaging.contracts.queue_routing_resolver import (
    QueueRoutingResolver,
)


ResolverScopeFactory = Callable[
    [],
    AsyncContextManager[QueueRoutingResolver],
]


class ScopedQueueRoutingResolver(QueueRoutingResolver):
    def __init__(self, scope_factory: ResolverScopeFactory) -> None:
        self._scope_factory = scope_factory

    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        async with self._scope_factory() as resolver:
            return await resolver.resolve_for_job(ingestion_job_id)
