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

        client = self._get_client()
        deployment = self._get_deployment()

        response = await client.embeddings.create(
            model=deployment,
            input=[
                chunk.content
                for chunk in chunks
            ],
        )

        return [
            EmbeddingResult(
                chunk_id=chunk.id,
                vector=list(item.embedding),
                model_name=(
                    self._model_name
                    or deployment
                ),
                dimension=len(item.embedding),
                token_count=None,
                status="success",
                error_message=None,
            )
            for chunk, item in zip(
                chunks,
                response.data,
                strict=True,
            )
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

        from shared.config.settings import settings

        self._deployment = (
            settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )

        return self._deployment
