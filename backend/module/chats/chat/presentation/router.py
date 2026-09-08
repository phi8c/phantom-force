from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from bootstrap.database import get_session
from module.chats.chat.application.dtos.request.chat_request import (
    ChatRequest,
)
from module.chats.chat.composition.factory import (
    create_chat_service,
)


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatHttpRequest(BaseModel):
    knowledge_space_id: UUID
    question: str = Field(min_length=1)


class ChatHttpResponse(BaseModel):
    answer: str
    intent: str | None = None
    seeds: list[dict]
    information: list[dict]


@router.post(
    "",
    response_model=ChatHttpResponse,
)
async def chat(
    request: ChatHttpRequest,
) -> ChatHttpResponse:

    async with get_session() as session:
        chat_service = create_chat_service(session)

        result = await chat_service.chat(
            ChatRequest(
                knowledge_space_id=request.knowledge_space_id,
                question=request.question,
            )
        )

    return ChatHttpResponse(
        answer=result.answer,
        intent=result.intent,
        seeds=result.seeds,
        information=result.information,
    )