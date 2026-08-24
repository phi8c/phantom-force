from dataclasses import dataclass
from uuid import UUID


@dataclass
class DocumentPipelineState:

    document_id: UUID

    chunks: list | None

    labels: list | None

    embeddings: list | None

    chunks_ready: bool

    classification_ready: bool

    embedding_ready: bool

    index_event_published: bool