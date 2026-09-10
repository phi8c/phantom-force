import logging
from time import perf_counter

from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkForEmbedding,
)
from module.ingest.embedding.domain.contracts.embedding_engine import (
    EmbeddingEngine,
    EmbeddingResult,
)
from module.ingest.embedding.domain.contracts.text_embedding_provider import (
    TextEmbeddingProvider,
)


logger = logging.getLogger(__name__)


class LegacyEmbeddingEngineAdapter(
    EmbeddingEngine,
    TextEmbeddingProvider,
):

    def __init__(
        self,
        client=None,
        deployment: str | None = None,
        model_name: str | None = None,
    ):
        self._client = client
        self._deployment = deployment
        self._model_name = model_name

    async def embed_batch(
        self,
        chunks: list[ChunkForEmbedding],
    ) -> list[EmbeddingResult]:

        if not chunks:
            return []

        vectors = await self.embed_texts(
            [
                chunk.content
                for chunk in chunks
            ],
        )

        return [
            EmbeddingResult(
                chunk_id=chunk.id,
                vector=vector,
                model_name=(
                    self._model_name
                    or self._get_deployment()
                ),
                dimension=len(vector),
                token_count=None,
                status="success",
                error_message=None,
            )
            for chunk, vector in zip(
                chunks,
                vectors,
                strict=True,
            )
        ]

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        started_at = perf_counter()
        logger.info(
            "[TEXT_EMBEDDING] request_start deployment=%s model=%s input_count=%s total_chars=%s",
            self._get_deployment(),
            self._model_name,
            len(texts),
            sum(len(text) for text in texts),
        )
        response = await self._get_client().embeddings.create(
            model=self._get_deployment(),
            input=texts,
        )

        vectors = [
            list(item.embedding)
            for item in response.data
        ]
        logger.info(
            "[TEXT_EMBEDDING] request_done deployment=%s elapsed_ms=%s vector_count=%s dimension=%s",
            self._get_deployment(),
            int((perf_counter() - started_at) * 1000),
            len(vectors),
            len(vectors[0]) if vectors else None,
        )
        return vectors

    def _get_client(self):

        if self._client is not None:
            return self._client

        from openai import AsyncAzureOpenAI

        from shared.config.settings import settings

        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        return self._client

    def _get_deployment(
        self,
    ) -> str:

        if self._deployment:
            return self._deployment

        raise ValueError(
            "Embedding deployment was not resolved "
            "from database configuration"
        )
