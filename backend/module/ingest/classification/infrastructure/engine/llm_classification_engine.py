from enum import Enum
import json
import logging
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


logger = logging.getLogger(__name__)


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
        response_format = self._response_format_from_config(
            response_format,
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

            logger.info(
                "classification llm_response chunk_id=%s model=%s response=%s",
                chunk.id,
                llm_result.model_code,
                llm_result.content,
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
                "response_contract": {
                    "sensitivity": {
                        "level": "integer >= 1",
                        "description": "string",
                    },
                    "document_type": "object",
                    "objects": "array",
                    "information_types": "array",
                    "information_fields": "array",
                    "topics": "array",
                    "information": {
                        "type": "array",
                        "item": {
                            "information_type": "string or null",
                            "summary": "string",
                            "data": "object or null",
                            "object_refs": (
                                "array of object identifier_code strings"
                            ),
                            "topic_refs": (
                                "array of topic code strings"
                            ),
                            "confidence": "number from 0 to 1 or null",
                        },
                    },
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _response_format_from_config(
        response_format: dict[str, Any] | None,
    ) -> dict[str, Any]:

        json_object_format = {
            "type": "json_object",
        }

        if response_format is None:
            return json_object_format

        if response_format.get("type") == "json_object":
            return response_format

        if (
            response_format.get("type") == "json_schema"
            and LLMClassificationEngine._has_canonical_sensitivity_schema(
                response_format,
            )
        ):
            return response_format

        logger.warning(
            "classification response_format_ignored reason=%s",
            "non_canonical_response_format",
        )
        return json_object_format

    @staticmethod
    def _has_canonical_sensitivity_schema(
        response_format: dict[str, Any],
    ) -> bool:

        json_schema = response_format.get(
            "json_schema",
        )
        if not isinstance(
            json_schema,
            dict,
        ):
            return False

        schema = json_schema.get(
            "schema",
        )
        if not isinstance(
            schema,
            dict,
        ):
            return False

        properties = schema.get(
            "properties",
        )
        if not isinstance(
            properties,
            dict,
        ):
            return False

        sensitivity = properties.get(
            "sensitivity",
        )
        if not isinstance(
            sensitivity,
            dict,
        ):
            return False

        sensitivity_properties = sensitivity.get(
            "properties",
        )
        if not isinstance(
            sensitivity_properties,
            dict,
        ):
            return False

        return {
            "level",
            "description",
        } <= set(sensitivity_properties)

    @staticmethod
    def _parse_json_response(
        content: str | None,
        chunk_id,
    ) -> dict[str, Any]:

        if not content:
            logger.error(
                "classification response_parse_failed chunk_id=%s raw_response=%s reason=%s",
                chunk_id,
                content,
                "empty_response",
            )
            raise ValueError(
                f"Empty classification response for chunk {chunk_id}",
            )

        try:
            parsed = json.loads(
                content,
            )
        except json.JSONDecodeError as exc:
            logger.exception(
                "classification response_parse_failed chunk_id=%s raw_response=%s reason=%s",
                chunk_id,
                content,
                "json_decode_error",
            )
            raise ValueError(
                "Invalid classification JSON response "
                f"for chunk {chunk_id}"
            ) from exc

        logger.debug(
            "classification parsed_response chunk_id=%s parsed=%s",
            chunk_id,
            parsed,
        )

        if not isinstance(
            parsed,
            dict,
        ):
            logger.error(
                "classification response_parse_failed chunk_id=%s raw_response=%s reason=%s parsed_type=%s",
                chunk_id,
                content,
                "non_object_json",
                type(parsed).__name__,
            )
            raise ValueError(
                "Classification response must be a JSON object "
                f"for chunk {chunk_id}",
            )

        return parsed
