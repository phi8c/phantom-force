import json
import logging
from time import perf_counter

from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.query_analysis.application.dtos.request.query_analysis_request import (
    QueryAnalysisRequest,
)
from module.launch_on_railway.query_analysis.application.dtos.response.query_analysis_result import (
    QueryAnalysisResult,
    QuerySeed,
)
from module.launch_on_railway.query_analysis.application.enums.query_analysis_enums import (
    QueryAnalysisModelCode,
    QueryAnalysisPromptCode,
    QueryAnalysisProviderCode,
)


logger = logging.getLogger(__name__)
MAX_QUERY_SEEDS = 15


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

        seeds = self._parse_seeds(
            result.get("seeds", []),
        )

        logger.info(
            "[QUERY_ANALYSIS] question=%s intent=%s candidate_seed_count=%s candidate_seeds=%s",
            request.question,
            result.get("intent", ""),
            len(seeds),
            [
                {
                    "object_code": seed.object_code,
                    "identifier_code": seed.identifier_code,
                    "information_type_code": (
                        seed.information_type_code
                    ),
                    "topic_codes": seed.topic_codes,
                    "constraints": seed.constraints,
                    "confidence": seed.confidence,
                }
                for seed in seeds
            ],
        )
        logger.info(
            "[QUERY_ANALYSIS] done elapsed_ms=%s",
            int((perf_counter() - started_at) * 1000),
        )

        return QueryAnalysisResult(
            intent=result.get("intent", ""),
            seeds=seeds,
            raw_response=result,
        )

    @staticmethod
    def _parse_seeds(
        raw_seeds,
    ) -> list[QuerySeed]:

        if not isinstance(raw_seeds, list):
            return []

        seeds: list[QuerySeed] = []
        for raw_seed in raw_seeds:
            if not isinstance(raw_seed, dict):
                continue

            topic_codes = raw_seed.get("topic_codes", [])
            if not isinstance(topic_codes, list):
                topic_codes = []

            constraints = raw_seed.get("constraints", {})
            if not isinstance(constraints, dict):
                constraints = {}

            confidence = raw_seed.get("confidence")
            if confidence is not None:
                try:
                    confidence = float(confidence)
                except (TypeError, ValueError):
                    confidence = None

            object_code = QueryAnalyzer._optional_str(
                raw_seed.get("object_code"),
            )
            information_type_code = QueryAnalyzer._optional_str(
                raw_seed.get("information_type_code"),
            )
            topic_codes = [
                str(topic_code)
                for topic_code in topic_codes
                if topic_code is not None
            ]

            if (
                object_code is None
                and information_type_code is None
                and not topic_codes
            ):
                continue
            identifier_code = QueryAnalyzer._optional_str(
                raw_seed.get("identifier_code"),
            )
            if object_code is None:
                identifier_code = None

            seeds.append(
                QuerySeed(
                    object_code=object_code,
                    identifier_code=identifier_code,
                    information_type_code=information_type_code,
                    topic_codes=topic_codes,
                    constraints=constraints,
                    confidence=confidence,
                )
            )

        return seeds[:MAX_QUERY_SEEDS]

    @staticmethod
    def _optional_str(
        value,
    ) -> str | None:

        if value is None:
            return None
        return str(value)

    @staticmethod
    def _build_user_prompt(
        request: QueryAnalysisRequest,
    ) -> str:

        return json.dumps(
            {
                "question": request.question,
                "response_contract": {
                    "intent": "string",
                    "seeds": {
                        "type": "array",
                        "item": {
                            "object_code": "string or null",
                            "identifier_code": "string or null",
                            "information_type_code": "string or null",
                            "topic_codes": "array of strings",
                            "constraints": "object",
                            "confidence": "number from 0 to 1 or null",
                        },
                        "max_items": MAX_QUERY_SEEDS,
                    },
                },
            },
            ensure_ascii=False,
        )
