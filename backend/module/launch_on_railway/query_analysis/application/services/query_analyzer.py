import json

from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.query_analysis.application.dtos.request.query_analysis_request import (
    QueryAnalysisRequest,
)
from module.launch_on_railway.query_analysis.application.dtos.response.query_analysis_result import (
    QueryAnalysisResult,
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
            seeds=result.get("seeds", []),
            raw_response=result,
        )

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
                            "information_type": "string or null",
                            "topic": "string or null",
                            "constraints": "object",
                            "confidence": "number from 0 to 1",
                        },
                    },
                },
            },
            ensure_ascii=False,
        )