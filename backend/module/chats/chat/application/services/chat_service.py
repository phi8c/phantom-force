import json
import logging
from time import perf_counter

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


logger = logging.getLogger(__name__)


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

        started_at = perf_counter()
        logger.info(
            "[CHAT_SERVICE] start knowledge_space_id=%s question_chars=%s",
            request.knowledge_space_id,
            len(request.question),
        )

        # 1. Analyze question
        step_started_at = perf_counter()
        logger.info("[CHAT_SERVICE] query_analysis_start")
        analysis = await self._query_analyzer.analyze(
            QueryAnalysisRequest(
                question=request.question,
            )
        )
        logger.info(
            "[CHAT_SERVICE] query_analysis_done elapsed_ms=%s intent=%s knowledge_request_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            analysis.intent,
            len(analysis.knowledge_requests),
        )

        # 2. Navigate structured knowledge
        step_started_at = perf_counter()
        logger.info("[CHAT_SERVICE] navigation_start")
        navigation = await self._navigation_service.navigate(
            knowledge_space_id=request.knowledge_space_id,
            question=request.question,
            analysis=analysis,
        )
        logger.info(
            "[CHAT_SERVICE] navigation_done elapsed_ms=%s information_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            len(navigation.items),
        )

        # 3. Load answer-generation prompt
        step_started_at = perf_counter()
        logger.info("[CHAT_SERVICE] answer_prompt_load_start")
        prompt = await self._prompt_provider.get_by_code(
            ChatPromptCode.ANSWER_GENERATION.value,
        )
        logger.info(
            "[CHAT_SERVICE] answer_prompt_load_done elapsed_ms=%s found=%s",
            int((perf_counter() - step_started_at) * 1000),
            prompt is not None,
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

        logger.info(
            "[ANSWER_GENERATION] information_count=%s",
            len(navigation.items),
        )

        # 4. Generate final answer
        step_started_at = perf_counter()
        answer_prompt = self._build_answer_prompt(
            question=request.question,
            navigation=navigation,
        )
        logger.info(
            "[CHAT_SERVICE] answer_generation_start user_prompt_chars=%s",
            len(answer_prompt),
        )
        llm_result = await self._llm_gateway.generate(
            provider_code=ChatProviderCode.AZURE_OPENAI.value,
            model_code=ChatModelCode.ANSWER_GENERATION.value,
            system_prompt=prompt.system_prompt,
            user_prompt=answer_prompt,
            response_format=response_format,
            config=config,
        )
        logger.info(
            "[CHAT_SERVICE] answer_generation_done elapsed_ms=%s finish_reason=%s usage=%s",
            int((perf_counter() - step_started_at) * 1000),
            llm_result.finish_reason,
            llm_result.usage,
        )

        if not llm_result.content:
            raise ValueError(
                "Empty answer generation response"
            )

        # 5. Build response
        response = ChatResponse(
            answer=llm_result.content,
            intent=analysis.intent,
            knowledge_requests=[
                {
                    "need": request.need,
                    "document_type_seeds": (
                        request.document_type_seeds
                    ),
                    "head_seeds": request.head_seeds,
                    "topic_seeds": request.topic_seeds,
                    "object_seeds": request.object_seeds,
                    "identifier_seeds": request.identifier_seeds,
                    "information_type_seeds": (
                        request.information_type_seeds
                    ),
                    "information_field_seeds": (
                        request.information_field_seeds
                    ),
                    "constraints": request.constraints,
                    "confidence": request.confidence,
                }
                for request in analysis.knowledge_requests
            ],
            information=[
                {
                    "information_id": item.information_id,
                    "information_type_code": (
                        item.information_type_code
                    ),
                    "summary": item.summary,
                    "data": item.data,
                    "object_refs": item.object_refs,
                    "topic_refs": item.topic_refs,
                    "source_refs": item.source_refs,
                    "confidence": item.confidence,
                }
                for item in navigation.items
            ],
        )
        logger.info(
            "[CHAT_SERVICE] done elapsed_ms=%s",
            int((perf_counter() - started_at) * 1000),
        )
        return response

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
                        "information_type_code": (
                            item.information_type_code
                        ),
                        "summary": item.summary,
                        "data": item.data,
                        "object_refs": item.object_refs,
                        "topic_refs": item.topic_refs,
                        "source_refs": item.source_refs,
                        "confidence": item.confidence,
                    }
                    for item in navigation.items
                ],
            },
            ensure_ascii=False,
            default=str,
        )
