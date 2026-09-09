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

        response = await self._get_client().embeddings.create(
            model=self._get_deployment(),
            input=texts,
        )

        return [
            list(item.embedding)
            for item in response.data
        ]

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
