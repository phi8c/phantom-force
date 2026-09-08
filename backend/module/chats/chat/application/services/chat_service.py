import json

from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.navigation.composition import (
    NavigationService,
)
from module.launch_on_railway.query_analysis.composition import (
    QueryAnalysisRequest,
    QueryAnalyzer,
)

from module.chats.chat.application.dtos.request.chat_request import (
    ChatRequest,
)
from module.chats.chat.application.dtos.response.chat_response import (
    ChatResponse,
)
from module.chats.chat.application.enums.chat_enums import (
    ChatModelCode,
    ChatPromptCode,
    ChatProviderCode,
)


class ChatService:

    def __init__(
        self,
        query_analyzer: QueryAnalyzer,
        navigation_service: NavigationService,
        prompt_provider: PromptProvider,
        llm_gateway: LLMGateway,
    ):
        self._query_analyzer = query_analyzer
        self._navigation_service = navigation_service
        self._prompt_provider = prompt_provider
        self._llm_gateway = llm_gateway

    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:

        # 1. Analyze question
        analysis = await self._query_analyzer.analyze(
            QueryAnalysisRequest(
                question=request.question,
            )
        )

        # 2. Navigate structured knowledge
        navigation = await self._navigation_service.navigate(
            knowledge_space_id=request.knowledge_space_id,
            analysis=analysis,
        )

        # 3. Load answer-generation prompt
        prompt = await self._prompt_provider.get_by_code(
            ChatPromptCode.ANSWER_GENERATION.value,
        )

        if prompt is None:
            raise ValueError(
                "Answer generation prompt not found or disabled"
            )

        config = dict(prompt.configuration or {})

        response_format = config.pop(
            "response_format",
            None,
        )

        # 4. Generate final answer
        llm_result = await self._llm_gateway.generate(
            provider_code=ChatProviderCode.AZURE_OPENAI.value,
            model_code=ChatModelCode.ANSWER_GENERATION.value,
            system_prompt=prompt.system_prompt,
            user_prompt=self._build_answer_prompt(
                question=request.question,
                navigation=navigation,
            ),
            response_format=response_format,
            config=config,
        )

        if not llm_result.content:
            raise ValueError(
                "Empty answer generation response"
            )

        # 5. Build response
        return ChatResponse(
            answer=llm_result.content,
            intent=analysis.intent,
            seeds=[
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
                for seed in analysis.seeds
            ],
            information=[
                {
                    "information_id": item.information_id,
                    "summary": item.summary,
                    "data": item.data,
                    "source_refs": item.source_refs,
                    "confidence": item.confidence,
                }
                for item in navigation.items
            ],
        )

    @staticmethod
    def _build_answer_prompt(
        *,
        question: str,
        navigation,
    ) -> str:

        return json.dumps(
            {
                "question": question,
                "information": [
                    {
                        "information_id": item.information_id,
                        "summary": item.summary,
                        "data": item.data,
                        "source_refs": item.source_refs,
                        "confidence": item.confidence,
                    }
                    for item in navigation.items
                ],
            },
            ensure_ascii=False,
            default=str,
        )