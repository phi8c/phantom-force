import json
import logging
from time import perf_counter

from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.query_analysis.application.dtos.request.query_analysis_request import (
    QueryAnalysisRequest,
)
from module.launch_on_railway.query_analysis.application.dtos.response.query_analysis_result import (
    KnowledgeRequest,
    QueryAnalysisResult,
)
from module.launch_on_railway.query_analysis.application.enums.query_analysis_enums import (
    QueryAnalysisModelCode,
    QueryAnalysisPromptCode,
    QueryAnalysisProviderCode,
)


logger = logging.getLogger(__name__)
MAX_KNOWLEDGE_REQUESTS = 5
MAX_DOCUMENT_TYPE_SEEDS = 3
MAX_HEAD_SEEDS = 3
MAX_TOPIC_SEEDS = 4
MAX_OBJECT_SEEDS = 4
MAX_IDENTIFIER_SEEDS = 3
MAX_INFORMATION_TYPE_SEEDS = 4
MAX_INFORMATION_FIELD_SEEDS = 4


class QueryAnalyzer:

    def __init__(
        self,
        prompt_provider: PromptProvider,
        llm_gateway: LLMGateway,
    ):
        self._prompt_provider = prompt_provider
        self._llm_gateway = llm_gateway

    async def analyze(
        self,
        request: QueryAnalysisRequest,
    ) -> QueryAnalysisResult:

        started_at = perf_counter()
        logger.info(
            "[QUERY_ANALYSIS] start question_chars=%s",
            len(request.question),
        )

        step_started_at = perf_counter()
        prompt = await self._prompt_provider.get_by_code(
            QueryAnalysisPromptCode.ANALYZE_QUERY.value,
        )
        logger.info(
            "[QUERY_ANALYSIS] prompt_load_done elapsed_ms=%s found=%s",
            int((perf_counter() - step_started_at) * 1000),
            prompt is not None,
        )

        if prompt is None:
            raise ValueError(
                "Query analysis prompt not found or disabled"
            )

        config = dict(prompt.configuration or {})

        response_format = config.pop(
            "response_format",
            {"type": "json_object"},
        )

        user_prompt = self._build_user_prompt(request)
        step_started_at = perf_counter()
        logger.info(
            "[QUERY_ANALYSIS] llm_start user_prompt_chars=%s",
            len(user_prompt),
        )
        llm_result = await self._llm_gateway.generate(
            provider_code=QueryAnalysisProviderCode.AZURE_OPENAI.value,
            model_code=QueryAnalysisModelCode.ANALYZE_QUERY.value,
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            response_format=response_format,
            config=config,
        )
        logger.info(
            "[QUERY_ANALYSIS] llm_done elapsed_ms=%s finish_reason=%s usage=%s",
            int((perf_counter() - step_started_at) * 1000),
            llm_result.finish_reason,
            llm_result.usage,
        )

        if not llm_result.content:
            raise ValueError(
                "Empty query analysis response"
            )

        result = json.loads(llm_result.content)

        if not isinstance(result, dict):
            raise ValueError(
                "Query analysis response must be a JSON object"
            )

        knowledge_requests = self._parse_knowledge_requests(
            result.get("knowledge_requests", []),
        )

        logger.info(
            "[QUERY_ANALYSIS] question=%s intent=%s knowledge_request_count=%s knowledge_requests=%s",
            request.question,
            result.get("intent", ""),
            len(knowledge_requests),
            [
                {
                    "need": item.need,
                    "document_type_seed_count": len(
                        item.document_type_seeds,
                    ),
                    "head_seed_count": len(item.head_seeds),
                    "topic_seed_count": len(item.topic_seeds),
                    "object_seed_count": len(item.object_seeds),
                    "identifier_seed_count": len(
                        item.identifier_seeds,
                    ),
                    "information_type_seed_count": len(
                        item.information_type_seeds,
                    ),
                    "information_field_seed_count": len(
                        item.information_field_seeds,
                    ),
                    "document_type_seeds": item.document_type_seeds,
                    "head_seeds": item.head_seeds,
                    "topic_seeds": item.topic_seeds,
                    "object_seeds": item.object_seeds,
                    "identifier_seeds": item.identifier_seeds,
                    "information_type_seeds": (
                        item.information_type_seeds
                    ),
                    "information_field_seeds": (
                        item.information_field_seeds
                    ),
                    "constraints": item.constraints,
                    "confidence": item.confidence,
                }
                for item in knowledge_requests
            ],
        )
        logger.info(
            "[QUERY_ANALYSIS] done elapsed_ms=%s",
            int((perf_counter() - started_at) * 1000),
        )

        return QueryAnalysisResult(
            intent=result.get("intent", ""),
            knowledge_requests=knowledge_requests,
            raw_response=result,
        )

    @classmethod
    def _parse_knowledge_requests(
        cls,
        raw_requests,
    ) -> list[KnowledgeRequest]:

        if not isinstance(raw_requests, list):
            return []

        knowledge_requests: list[KnowledgeRequest] = []
        for raw_item in raw_requests:
            if not isinstance(raw_item, dict):
                continue

            need = cls._optional_non_empty_str(
                raw_item.get("need"),
            )
            if need is None:
                continue

            constraints = raw_item.get("constraints", {})
            if not isinstance(constraints, dict):
                constraints = {}

            knowledge_request = KnowledgeRequest(
                need=need,
                document_type_seeds=cls._seed_list(
                    raw_item.get("document_type_seeds", []),
                    max_items=MAX_DOCUMENT_TYPE_SEEDS,
                ),
                head_seeds=cls._seed_list(
                    raw_item.get("head_seeds", []),
                    max_items=MAX_HEAD_SEEDS,
                ),
                topic_seeds=cls._seed_list(
                    raw_item.get("topic_seeds", []),
                    max_items=MAX_TOPIC_SEEDS,
                ),
                object_seeds=cls._seed_list(
                    raw_item.get("object_seeds", []),
                    max_items=MAX_OBJECT_SEEDS,
                ),
                identifier_seeds=cls._seed_list(
                    raw_item.get("identifier_seeds", []),
                    max_items=MAX_IDENTIFIER_SEEDS,
                ),
                information_type_seeds=cls._seed_list(
                    raw_item.get("information_type_seeds", []),
                    max_items=MAX_INFORMATION_TYPE_SEEDS,
                ),
                information_field_seeds=cls._seed_list(
                    raw_item.get("information_field_seeds", []),
                    max_items=MAX_INFORMATION_FIELD_SEEDS,
                ),
                constraints=constraints,
                confidence=cls._confidence(
                    raw_item.get("confidence"),
                ),
            )

            if not cls._has_semantic_seed(knowledge_request):
                logger.warning(
                    "[QUERY_ANALYSIS] knowledge_request_without_semantic_seed need=%s",
                    knowledge_request.need,
                )

            knowledge_requests.append(knowledge_request)

        return knowledge_requests[:MAX_KNOWLEDGE_REQUESTS]

    @staticmethod
    def _seed_list(
        value,
        *,
        max_items: int,
    ) -> list[str]:

        if not isinstance(value, list):
            return []

        result = []
        seen = set()
        for item in value:
            text = QueryAnalyzer._optional_non_empty_str(item)
            if text is None or text in seen:
                continue
            seen.add(text)
            result.append(text)
            if len(result) >= max_items:
                break
        return result

    @staticmethod
    def _confidence(value) -> float | None:

        if value is None:
            return None
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None
        if not 0.0 <= confidence <= 1.0:
            return None
        return confidence

    @staticmethod
    def _has_semantic_seed(
        knowledge_request: KnowledgeRequest,
    ) -> bool:

        return any(
            (
                knowledge_request.document_type_seeds,
                knowledge_request.head_seeds,
                knowledge_request.topic_seeds,
                knowledge_request.object_seeds,
                knowledge_request.identifier_seeds,
                knowledge_request.information_type_seeds,
                knowledge_request.information_field_seeds,
            )
        )

    @staticmethod
    def _optional_non_empty_str(
        value,
    ) -> str | None:

        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _build_user_prompt(
        request: QueryAnalysisRequest,
    ) -> str:

        return json.dumps(
            {
                "question": request.question,
                "response_contract": {
                    "intent": "string",
                    "knowledge_requests": {
                        "type": "array",
                        "max_items": MAX_KNOWLEDGE_REQUESTS,
                        "item": {
                            "need": "string",
                            "document_type_seeds": (
                                "array of strings, max 3"
                            ),
                            "head_seeds": (
                                "array of strings, max 3"
                            ),
                            "topic_seeds": (
                                "array of strings, max 4"
                            ),
                            "object_seeds": (
                                "array of strings, max 4"
                            ),
                            "identifier_seeds": (
                                "array of strings, max 3"
                            ),
                            "information_type_seeds": (
                                "array of strings, max 4"
                            ),
                            "information_field_seeds": (
                                "array of strings, max 4"
                            ),
                            "constraints": "object",
                            "confidence": "number from 0 to 1 or null",
                        },
                    },
                },
            },
            ensure_ascii=False,
        )
