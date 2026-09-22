from uuid import UUID
import logging
from time import perf_counter
from shared.logging.chat_diagnostics import print_chat_trace

from fastapi import APIRouter
from pydantic import BaseModel, Field

from bootstrap.database import get_session

from module.chats.chat.application.dtos.request.chat_request import (
    ChatRequest,
)
from module.chats.chat.application.services.chat_service import (
    ChatService,
)

from module.ai.llm.composition import (
    create_llm_gateway,
)
from module.prompt.composition import (
    create_prompt_provider,
)
from module.ingest.knowledge.composition import (
    create_knowledge_reader,
)
from module.launch_on_railway.query_analysis.composition import (
    create_query_analyzer,
)
from module.launch_on_railway.knowledge_selection.composition import (
    create_knowledge_selector,
)
from module.launch_on_railway.navigation.composition import (
    create_navigation_service,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatHttpRequest(BaseModel):
    knowledge_space_id: UUID
    question: str = Field(
        min_length=1,
    )


class ChatHttpResponse(BaseModel):
    answer: str
    intent: str | None = None
    knowledge_requests: list[dict]
    information: list[dict]


@router.post(
    "",
    response_model=ChatHttpResponse,
)
async def chat(
    request: ChatHttpRequest,
) -> ChatHttpResponse:

    started_at = perf_counter()
    logger.info(
        "[CHAT_API] request_start knowledge_space_id=%s question_chars=%s",
        request.knowledge_space_id,
        len(request.question),
    )
    print_chat_trace("REQUEST", request.model_dump(mode="json"))

    async with get_session() as session:

        # Shared dependencies
        prompt_provider = create_prompt_provider(
            session,
        )

        llm_gateway = create_llm_gateway(
            session,
        )

        # LR - Query Analysis
        query_analyzer = create_query_analyzer(
            prompt_provider=prompt_provider,
            llm_gateway=llm_gateway,
        )

        # Knowledge
        knowledge_reader = create_knowledge_reader(
            session,
        )

        # LR - Knowledge Selection
        knowledge_selector = create_knowledge_selector(
            prompt_provider=prompt_provider,
            llm_gateway=llm_gateway,
        )

        # LR - Navigation
        navigation_service = create_navigation_service(
            knowledge_reader=knowledge_reader,
            knowledge_selector=knowledge_selector,
        )

        # Chat
        chat_service = ChatService(
            query_analyzer=query_analyzer,
            navigation_service=navigation_service,
            prompt_provider=prompt_provider,
            llm_gateway=llm_gateway,
        )

        result = await chat_service.chat(
            ChatRequest(
                knowledge_space_id=request.knowledge_space_id,
                question=request.question,
            )
        )

    logger.info(
        "[CHAT_API] request_done knowledge_space_id=%s elapsed_ms=%s",
        request.knowledge_space_id,
        int((perf_counter() - started_at) * 1000),
    )

    response = ChatHttpResponse(
        answer=result.answer,
        intent=result.intent,
        knowledge_requests=result.knowledge_requests,
        information=result.information,
    )
    print_chat_trace("HTTP_RESPONSE", response.model_dump(mode="json"))
    return response
