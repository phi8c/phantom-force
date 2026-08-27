from __future__ import annotations

import json
import logging
from typing import Iterator
from uuid import UUID

from app.application.classification.model_provider import (
    ModelConfig,
    get_model_set,
)
from app.application.classification.ollama_client import (
    ModelCallError,
    call_model,
)
from app.application.classification.prompt_provider import (
    build_prompt,
)
from app.application.classification.schemas import (
    Chunk,
    ClassificationResult,
)
from app.application.classification.token_counter import (
    estimate_tokens_for_chunks,
)

logger = logging.getLogger(__name__)

PROMPT_OVERHEAD_TOKENS = 500
OUTPUT_RESERVED_TOKENS = 1000


class ClassificationEngine:

    def __init__(
        self,
        purpose: str = "classification",
    ):
        self.purpose = purpose
        self.model_set: list[ModelConfig] = get_model_set(
            purpose,
        )
        
    

    async def classify_batch(
        self,
        chunks: list[Chunk],
    ) -> list[ClassificationResult]:

        if not chunks:
            return []

        primary_model = self.model_set[0]

        max_allowed_tokens = (
            primary_model.max_context_tokens
            - PROMPT_OVERHEAD_TOKENS
            - OUTPUT_RESERVED_TOKENS
        )

        batch_tokens = estimate_tokens_for_chunks(
            chunks,
        )

        if batch_tokens <= max_allowed_tokens:
            return await self._classify_single_batch(
                chunks,
            )

        logger.info(
            "Batch %d chunk (~%d token) vượt giới hạn ~%d token của model '%s'.",
            len(chunks),
            batch_tokens,
            max_allowed_tokens,
            primary_model.name,
        )

        results: list[ClassificationResult] = []

        for sub_batch in self._split_batch(
            chunks,
            max_allowed_tokens,
        ):
            results.extend(
                await self._classify_single_batch(
                    sub_batch,
                )
            )

        return results

    def _split_batch(
        self,
        chunks: list[Chunk],
        max_allowed_tokens: int,
    ) -> Iterator[list[Chunk]]:

        current: list[Chunk] = []

        current_tokens = 0

        for chunk in chunks:

            chunk_tokens = estimate_tokens_for_chunks(
                [chunk],
            )

            if (
                current
                and current_tokens + chunk_tokens > max_allowed_tokens
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

    async def _classify_single_batch(
        self,
        chunks: list[Chunk],
    ) -> list[ClassificationResult]:

        prompt = build_prompt(
        chunks,
        purpose=self.purpose,
    )

        raw_response, model_name = await self._call_with_fallback(
            prompt,
        )

        return self._parse_response(
            raw_response,
            chunks,
            model_name,
        )

    async def _call_with_fallback(
    self,
    prompt: str,
) -> tuple[str, str]:

        last_error: Exception | None = None

        for model in self.model_set:

            try:

                logger.info(
                    "Gọi model '%s' (provider=%s).",
                    model.name,
                    model.provider,
                )
               

                response = await call_model(
                   
                    model,
                    prompt,
                )
                return response, model.name

            except ModelCallError as e:

                logger.warning(
                    "Model '%s' lỗi, fallback. Error=%s",
                    model.name,
                    e,
                )

                last_error = e

        raise RuntimeError(
            f"Tất cả model trong bộ model '{self.purpose}' đều thất bại."
        ) from last_error

    def _parse_response(
    self,
    raw_response: str,
    chunks: list[Chunk],
    model_name: str,
) -> list[ClassificationResult]:
        
        print("=" * 80)
        print("DEBUG CLASSIFICATION PARSE")
        print("chunks type:", type(chunks))
        print("chunks:", chunks)

        if chunks:
            print("first chunk type:", type(chunks[0]))
            print("first chunk:", chunks[0])

        print("=" * 80)

        chunk_ids = {
            chunk.id
            for chunk in chunks
        }

        try:
            parsed = json.loads(
                raw_response,
            )

        except json.JSONDecodeError:

            logger.error(
                "Không parse được JSON. Raw response: %s",
                raw_response,
            )

            return [
                ClassificationResult(
                    chunk_id=chunk.id,
                    label="unknown",
                    raw_response=raw_response,
                    model_name=model_name,
                )
                for chunk in chunks
            ]

        results: list[ClassificationResult] = []

        for item in parsed:

            try:
                chunk_id = UUID(
                    item["chunk_id"],
                )
            except (KeyError, ValueError, TypeError):
                continue

            if chunk_id not in chunk_ids:
                continue

            results.append(
                ClassificationResult(
                    chunk_id=chunk_id,
                    label=item.get(
                        "label",
                        "unknown",
                    ),
                    confidence=item.get(
                        "confidence",
                    ),
                    raw_response=raw_response,
                    model_name=model_name,
                )
            )

        returned_ids = {
            result.chunk_id
            for result in results
        }

        for chunk in chunks:

            if chunk.id not in returned_ids:

                results.append(
                    ClassificationResult(
                        chunk_id=chunk.id,
                        label="unknown",
                        raw_response=raw_response,
                        model_name=model_name,
                    )
                )

        return results
