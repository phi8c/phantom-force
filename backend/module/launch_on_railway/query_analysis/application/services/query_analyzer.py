import json

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

        prompt = await self._prompt_provider.get_by_code(
            QueryAnalysisPromptCode.ANALYZE_QUERY.value,
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

        llm_result = await self._llm_gateway.generate(
            provider_code=QueryAnalysisProviderCode.AZURE_OPENAI.value,
            model_code=QueryAnalysisModelCode.ANALYZE_QUERY.value,
            system_prompt=prompt.system_prompt,
            user_prompt=self._build_user_prompt(request),
            response_format=response_format,
            config=config,
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

        return QueryAnalysisResult(
            intent=result.get("intent", ""),
            seeds=self._parse_seeds(
                result.get("seeds", []),
            ),
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

            object_code = raw_seed.get("object_code")
            if not object_code:
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

            seeds.append(
                QuerySeed(
                    object_code=str(object_code),
                    identifier_code=(
                        QueryAnalyzer._optional_str(
                            raw_seed.get("identifier_code"),
                        )
                    ),
                    information_type_code=(
                        QueryAnalyzer._optional_str(
                            raw_seed.get("information_type_code"),
                        )
                    ),
                    topic_codes=[
                        str(topic_code)
                        for topic_code in topic_codes
                        if topic_code is not None
                    ],
                    constraints=constraints,
                    confidence=confidence,
                )
            )

        return seeds

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
                            "object_code": "string",
                            "identifier_code": "string or null",
                            "information_type_code": "string or null",
                            "topic_codes": "array of strings",
                            "constraints": "object",
                            "confidence": "number from 0 to 1 or null",
                        },
                    },
                },
            },
            ensure_ascii=False,
        )
