from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.messaging.composition import IngestConsumers, IngestDispatchers

from ..dispatchers import (
    RabbitMQChunkingDispatcher,
    RabbitMQClassificationDispatcher,
    RabbitMQDiscoveryDispatcher,
    RabbitMQDownloadDispatcher,
    RabbitMQEmbeddingDispatcher,
    RabbitMQExtractionDispatcher,
)
from ..transport import RabbitMQTransport


def _settings() -> Any:
    from shared.config.settings import settings

    return settings


@dataclass(frozen=True, slots=True)
class RabbitMQConsumerResources:
    consumers: IngestConsumers
    transport: RabbitMQTransport

    async def close(self) -> None:
        await self.transport.close()


@dataclass(frozen=True, slots=True)
class RabbitMQProducerResources:
    dispatchers: IngestDispatchers
    transport: RabbitMQTransport

    async def close(self) -> None:
        await self.transport.close()


async def create_rabbitmq_consumers() -> RabbitMQConsumerResources:
    configuration = _settings()
    transport = RabbitMQTransport(configuration.RABBITMQ_URL)
    try:
        consumers = IngestConsumers(
            discovery=await transport.create_consumer(
                configuration.RABBITMQ_DISCOVERY_QUEUE
            ),
            download=await transport.create_consumer(
                configuration.RABBITMQ_DOWNLOAD_QUEUE
            ),
            extraction=await transport.create_consumer(
                configuration.RABBITMQ_EXTRACT_QUEUE
            ),
            chunking=await transport.create_consumer(
                configuration.RABBITMQ_CHUNK_QUEUE
            ),
            embedding=await transport.create_consumer(
                configuration.RABBITMQ_EMBED_QUEUE
            ),
            classification=await transport.create_consumer(
                configuration.RABBITMQ_CLASSIFY_QUEUE
            ),
        )
    except Exception:
        await transport.close()
        raise
    return RabbitMQConsumerResources(
        consumers=consumers,
        transport=transport,
    )


async def create_rabbitmq_dispatchers(
    resources: RabbitMQConsumerResources,
) -> IngestDispatchers:
    configuration = _settings()
    publisher = await resources.transport.create_publisher()
    return IngestDispatchers(
        discovery=RabbitMQDiscoveryDispatcher(
            publisher,
            configuration.RABBITMQ_DISCOVERY_QUEUE,
        ),
        download=RabbitMQDownloadDispatcher(
            publisher,
            configuration.RABBITMQ_DOWNLOAD_QUEUE,
        ),
        extraction=RabbitMQExtractionDispatcher(
            publisher,
            configuration.RABBITMQ_EXTRACT_QUEUE,
        ),
        chunking=RabbitMQChunkingDispatcher(
            publisher,
            configuration.RABBITMQ_CHUNK_QUEUE,
        ),
        embedding=RabbitMQEmbeddingDispatcher(
            publisher,
            configuration.RABBITMQ_EMBED_QUEUE,
        ),
        classification=RabbitMQClassificationDispatcher(
            publisher,
            configuration.RABBITMQ_CLASSIFY_QUEUE,
        ),
    )


async def create_rabbitmq_producer() -> RabbitMQProducerResources:
    configuration = _settings()
    transport = RabbitMQTransport(configuration.RABBITMQ_URL)
    try:
        publisher = await transport.create_publisher()
        dispatchers = IngestDispatchers(
            discovery=RabbitMQDiscoveryDispatcher(
                publisher,
                configuration.RABBITMQ_DISCOVERY_QUEUE,
            ),
            download=RabbitMQDownloadDispatcher(
                publisher,
                configuration.RABBITMQ_DOWNLOAD_QUEUE,
            ),
            extraction=RabbitMQExtractionDispatcher(
                publisher,
                configuration.RABBITMQ_EXTRACT_QUEUE,
            ),
            chunking=RabbitMQChunkingDispatcher(
                publisher,
                configuration.RABBITMQ_CHUNK_QUEUE,
            ),
            embedding=RabbitMQEmbeddingDispatcher(
                publisher,
                configuration.RABBITMQ_EMBED_QUEUE,
            ),
            classification=RabbitMQClassificationDispatcher(
                publisher,
                configuration.RABBITMQ_CLASSIFY_QUEUE,
            ),
        )
    except Exception:
        await transport.close()
        raise
    return RabbitMQProducerResources(dispatchers, transport)
