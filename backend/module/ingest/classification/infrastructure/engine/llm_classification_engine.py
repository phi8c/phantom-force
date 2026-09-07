from enum import Enum
import json
from typing import Any

from module.ai.llm.composition import (
    LLMGateway,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
)
from module.ingest.classification.domain.contracts.classification_engine import (
    ClassificationEngine,
    ClassificationResult,
)
from module.prompt.composition import (
    PromptProvider,
)


class ClassificationPromptCode(
    Enum,
):
    ANALYZE_CHUNK = (
        "ingest.classification.analyze_chunk"
    )


class ClassificationProviderCode(
    Enum,
):
    AZURE_OPENAI = "azure_openai"


class ClassificationModelCode(
    Enum,
):
    ANALYZE_CHUNK = "gpt-5.1"


class LLMClassificationEngine(
    ClassificationEngine,
):

    def __init__(
        self,
        prompt_provider: PromptProvider,
        llm_gateway: LLMGateway,
    ):
        self._prompt_provider = prompt_provider
        self._llm_gateway = llm_gateway

    async def classify_batch(
        self,
        chunks: list[ChunkForClassification],
    ) -> list[ClassificationResult]:

        if not chunks:
            return []

        prompt = await self._prompt_provider.get_by_code(
            ClassificationPromptCode.ANALYZE_CHUNK.value,
        )

        if prompt is None:
            raise ValueError(
                "Classification prompt not found or disabled",
            )

        config = dict(
            prompt.configuration or {},
        )
        response_format = config.pop(
            "response_format",
            None,
        )

        results: list[ClassificationResult] = []

        for chunk in chunks:
            llm_result = await self._llm_gateway.generate(
                provider_code=(
                    ClassificationProviderCode
                    .AZURE_OPENAI
                    .value
                ),
                model_code=(
                    ClassificationModelCode
                    .ANALYZE_CHUNK
                    .value
                ),
                system_prompt=prompt.system_prompt,
                user_prompt=self._build_user_prompt(
                    chunk,
                ),
                response_format=response_format,
                config=config,
            )

            raw_response = self._parse_json_response(
                llm_result.content,
                chunk.id,
            )

            results.append(
                ClassificationResult(
                    chunk_id=chunk.id,
                    model_name=llm_result.model_code,
                    raw_response=raw_response,
                )
            )

        return results

    @staticmethod
    def _build_user_prompt(
        chunk: ChunkForClassification,
    ) -> str:

        return json.dumps(
            {
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "metadata": chunk.metadata,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_json_response(
        content: str | None,
        chunk_id,
    ) -> dict[str, Any]:

        if not content:
            raise ValueError(
                f"Empty classification response for chunk {chunk_id}",
            )

        try:
            parsed = json.loads(
                content,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid classification JSON response "
                f"for chunk {chunk_id}"
            ) from exc

        if not isinstance(
            parsed,
            dict,
        ):
            raise ValueError(
                "Classification response must be a JSON object "
                f"for chunk {chunk_id}",
            )

        return parsed
