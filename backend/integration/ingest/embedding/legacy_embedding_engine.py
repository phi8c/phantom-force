from app.application.embedding.engine import (
    EmbeddingEngine as LegacyEmbeddingEngine,
)
from app.application.embedding.schemas import (
    Chunk as LegacyChunk,
)

from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkForEmbedding,
)
from module.ingest.embedding.domain.contracts.embedding_engine import (
    EmbeddingEngine,
    EmbeddingResult,
)


class LegacyEmbeddingEngineAdapter(
    EmbeddingEngine,
):

    def __init__(
        self,
        engine: LegacyEmbeddingEngine | None = None,
    ):
        self._engine = engine or LegacyEmbeddingEngine()

    async def embed_batch(
        self,
        chunks: list[ChunkForEmbedding],
    ) -> list[EmbeddingResult]:

        legacy_chunks = [
            LegacyChunk(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]

        results = self._engine.embed_batch(
            legacy_chunks,
        )

        return [
            EmbeddingResult(
                chunk_id=result.chunk_id,
                vector=result.vector,
                model_name=result.model_name,
                dimension=result.dimension,
                token_count=result.token_count,
                status=result.status,
                error_message=result.error_message,
            )
            for result in results
        ]
