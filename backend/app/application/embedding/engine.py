"""
EmbeddingEngine

Luồng xử lý:
1. Nhận vào 1 batch chunk (thường 10-20 chunk, từ ingest flow gửi tới).
2. Với từng chunk:
   - Rỗng / chỉ có khoảng trắng -> skip, không gọi API (status=skipped_empty).
   - Vượt max_input_tokens (8191 với text-embedding-3-small) -> truncate cho vừa.
3. Check tổng token + số lượng item của batch đã lọc, nếu vượt ngưỡng an toàn
   cho 1 request -> chia thành nhiều sub-batch, gọi API tuần tự.
4. Gọi OpenAI Embeddings API (1 request cho nhiều text cùng lúc), map kết quả
   vector về đúng chunk theo thứ tự.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from app.application.chunking.contracts.token_counter import (
    TokenCounter,
)
from app.application.embedding.model_provider import (
    EmbeddingModelConfig,
    get_embedding_model,
)
from app.application.embedding.openai_client import (
    EmbeddingCallError,
    call_embedding_api,
)
from app.application.embedding.schemas import (
    Chunk,
    EmbeddingResult,
)
from app.application.embedding.token_utils import (
    truncate_to_max_tokens,
)

logger = logging.getLogger(__name__)

MAX_TOTAL_TOKENS_PER_REQUEST = 300_000
MAX_ITEMS_PER_REQUEST = 2048


def _default_token_counter(
    model_name: str,
) -> TokenCounter:
    from app.infrastructure.tokenizers.tiktoken_counter import (
        TiktokenCounter,
    )

    return TiktokenCounter(
        model_name=model_name,
    )


class EmbeddingEngine:

    def __init__(
        self,
        purpose: str = "embedding",
        token_counter: TokenCounter | None = None,
    ) -> None:

        self.model: EmbeddingModelConfig = get_embedding_model(
            purpose,
        )

        self.token_counter: TokenCounter = (
            token_counter
            if token_counter is not None
            else _default_token_counter(
                self.model.name,
            )
        )

    def embed_batch(
        self,
        chunks: list[Chunk],
    ) -> list[EmbeddingResult]:

        if not chunks:
            return []

        results: list[EmbeddingResult] = []

        embeddable: list[Chunk] = []

        for chunk in chunks:

            text = chunk.content.strip()

            if not text:

                results.append(
                    EmbeddingResult(
                        chunk_id=chunk.id,
                        vector=None,
                        model_name=self.model.name,
                        status="skipped_empty",
                    )
                )

                continue

            token_count = self.token_counter.count(
                text,
            )

            if token_count > self.model.max_input_tokens:

                logger.warning(
                    "Chunk '%s' có %d token, vượt giới hạn %d token của model '%s' -> truncate.",
                    chunk.id,
                    token_count,
                    self.model.max_input_tokens,
                    self.model.name,
                )

                text = truncate_to_max_tokens(
                    text=text,
                    token_counter=self.token_counter,
                    max_tokens=self.model.max_input_tokens,
                )

            embeddable.append(
                Chunk(
                    id=chunk.id,
                    content=text,
                    metadata=chunk.metadata,
                )
            )

        for sub_batch in self._split_batch(
            embeddable,
        ):
            results.extend(
                self._embed_single_batch(
                    sub_batch,
                )
            )

        return results

    def _split_batch(
        self,
        chunks: list[Chunk],
    ) -> Iterator[list[Chunk]]:

        current: list[Chunk] = []

        current_tokens = 0

        for chunk in chunks:

            chunk_tokens = self.token_counter.count(
                chunk.content,
            )

            would_exceed_items = (
                len(current) + 1 > MAX_ITEMS_PER_REQUEST
            )

            would_exceed_tokens = (
                bool(current)
                and current_tokens + chunk_tokens
                > MAX_TOTAL_TOKENS_PER_REQUEST
            )

            if current and (
                would_exceed_items
                or would_exceed_tokens
            ):

                yield current

                current = []

                current_tokens = 0

            current.append(
                chunk,
            )

            current_tokens += chunk_tokens

        if current:
            yield current

    def _embed_single_batch(
        self,
        chunks: list[Chunk],
    ) -> list[EmbeddingResult]:

        if not chunks:
            return []

        texts = [
            chunk.content
            for chunk in chunks
        ]

        try:

            vectors = call_embedding_api(
                self.model,
                texts,
            )

        except EmbeddingCallError as e:

            logger.error(
                "Embedding batch thất bại: %s",
                e,
            )

            return [
                EmbeddingResult(
                    chunk_id=chunk.id,
                    vector=None,
                    model_name=self.model.name,
                    status="error",
                    error_message=str(e),
                )
                for chunk in chunks
            ]

        results: list[EmbeddingResult] = []

        for chunk, vector in zip(
            chunks,
            vectors,
        ):

            results.append(
                EmbeddingResult(
                    chunk_id=chunk.id,
                    vector=vector,
                    model_name=self.model.name,
                    dimension=len(vector),
                    token_count=self.token_counter.count(
                        chunk.content,
                    ),
                    status="ok",
                )
            )

        return results