from app.application.orchestration.event_dispatcher import (
    EventDispatcher,
)

from app.application.orchestration.event_registry import (
    EventRegistry,
)

from app.application.orchestration.event_resolver import (
    EventResolver,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)

from app.domain.events.classification_completed_event import (
    ClassificationCompletedEvent,
)

from app.domain.events.document_extracted_event import (
    DocumentExtractedEvent,
)

from app.domain.events.document_ready_for_index_event import (
    DocumentReadyForIndexEvent,
)

from app.domain.events.embedding_completed_event import (
    EmbeddingCompletedEvent,
)

from app.application.orchestration.handlers.chunk_handler import (
    ChunkHandler,
)

from app.application.orchestration.handlers.save_extraction_handler import (
    SaveExtractionHandler,
)



from app.application.orchestration.handlers.classify_handler import (
    ClassifyHandler,
)

from app.application.orchestration.handlers.embed_handler import (
    EmbedHandler,
)

from app.application.orchestration.handlers.classification_completed_handler import (
    ClassificationCompletedHandler,
)

from app.application.orchestration.handlers.embedding_completed_handler import (
    EmbeddingCompletedHandler,
)

from app.application.orchestration.handlers.document_ready_for_index_handler import (
    DocumentReadyForIndexHandler,
)
from app.application.orchestration.handlers.chunk_created_state_handler import ChunkCreatedStateHandler

from app.domain.events.document_downloaded_event import (
    DocumentDownloadedEvent,
)
from app.application.orchestration.handlers.extract_handler import ExtractHandler



from app.application.orchestration.event_deserializer import (
    EventDeserializer,
)
from app.application.orchestration.event_processor import EventProcessor

def build_event_resolver() -> EventResolver:

    resolver = EventResolver()

    resolver.register(
        "DocumentExtractedEvent",
        DocumentExtractedEvent,
    )

    resolver.register(
        "ChunkCreatedEvent",
        ChunkCreatedEvent,
    )

    resolver.register(
        "ClassificationCompletedEvent",
        ClassificationCompletedEvent,
    )

    resolver.register(
        "EmbeddingCompletedEvent",
        EmbeddingCompletedEvent,
    )

    resolver.register(
        "DocumentReadyForIndexEvent",
        DocumentReadyForIndexEvent,
    )
    
    resolver.register(
    "DocumentDownloadedEvent",
    DocumentDownloadedEvent,
)
   

    return resolver


def build_event_registry(
    *,
     document_extractor,
    chunking_engine,
    extraction_repository,
    chunk_repository,
    classifier,
    embedding_provider,
    state_repository,
    indexing_engine,
    event_bus,
) -> EventRegistry:

    registry = EventRegistry()

    registry.register(
        DocumentExtractedEvent,
        ChunkHandler(
            chunking_engine=chunking_engine,
            event_bus=event_bus,
        ),
    )

    registry.register(
        DocumentExtractedEvent,
        SaveExtractionHandler(
            extraction_repository=(
                extraction_repository
            ),
        ),
    )

    registry.register(
        ChunkCreatedEvent,
        ClassifyHandler(
            classifier=classifier,
            event_bus=event_bus,
        ),
    )

    registry.register(
        ChunkCreatedEvent,
        EmbedHandler(
            embedding_provider=(
                embedding_provider
            ),
            event_bus=event_bus,
        ),
    )

    
    registry.register(
        ClassificationCompletedEvent,
        ClassificationCompletedHandler(
            state_repository=(
                state_repository
            ),
            event_bus=event_bus,
        ),
    )

    registry.register(
        EmbeddingCompletedEvent,
        EmbeddingCompletedHandler(
            state_repository=(
                state_repository
            ),
            event_bus=event_bus,
        ),
    )

    registry.register(
    DocumentReadyForIndexEvent,
    DocumentReadyForIndexHandler(
        state_repository=state_repository,
        indexing_engine=indexing_engine,
    ),
)
    
    registry.register(
    ChunkCreatedEvent,
    ChunkCreatedStateHandler(
        state_repository=state_repository,
    ),
)
    registry.register(
    DocumentDownloadedEvent,
    ExtractHandler(
        document_extractor=document_extractor,
        event_bus=event_bus,
    ),
)
   
    
    

    return registry


def build_event_dispatcher(
    registry: EventRegistry,
) -> EventDispatcher:

    return EventDispatcher(
        registry=registry,
    )
    
def build_event_processor(
    resolver: EventResolver,
    dispatcher: EventDispatcher,
) -> EventProcessor:

    return EventProcessor(
    resolver=resolver,
    dispatcher=dispatcher,
    deserializer=(
        EventDeserializer()
    ),
)