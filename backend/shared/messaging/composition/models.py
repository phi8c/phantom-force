from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from module.ingest.chunking.domain.contracts.chunking_dispatcher import (
    ChunkingDispatcher,
)
from module.ingest.classification.domain.contracts.classification_dispatcher import (
    ClassificationDispatcher,
)
from module.ingest.discovery.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher,
)
from module.ingest.download.domain.contracts.download_dispatcher import (
    DownloadDispatcher,
)
from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)
from module.ingest.extraction.domain.contracts.extraction_dispatcher import (
    ExtractionDispatcher,
)

from ..contracts.consumer import MessageConsumer


CloseCallback = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class IngestConsumers:
    discovery: MessageConsumer
    download: MessageConsumer
    extraction: MessageConsumer
    chunking: MessageConsumer
    embedding: MessageConsumer
    classification: MessageConsumer


@dataclass(frozen=True, slots=True)
class IngestDispatchers:
    discovery: DiscoveryDispatcher
    download: DownloadDispatcher
    extraction: ExtractionDispatcher
    chunking: ChunkingDispatcher
    embedding: EmbeddingDispatcher
    classification: ClassificationDispatcher


@dataclass(frozen=True, slots=True)
class IngestProducer:
    dispatchers: IngestDispatchers
    _close_callback: CloseCallback = field(repr=False)

    async def close(self) -> None:
        await self._close_callback()


@dataclass(frozen=True, slots=True)
class IngestMessaging:
    consumers: IngestConsumers
    dispatchers: IngestDispatchers
    _close_callback: CloseCallback = field(repr=False)

    async def close(self) -> None:
        await self._close_callback()
