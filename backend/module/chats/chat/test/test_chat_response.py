from module.chats.chat.application.dtos.response.chat_response import (
    ChatResponse,
)


def test_chat_response_exposes_knowledge_requests_with_legacy_seed_alias():
    response = ChatResponse(
        answer="Done",
        knowledge_requests=[
            {
                "need": "Compare policies",
            }
        ],
    )

    assert response.knowledge_requests == [
        {
            "need": "Compare policies",
        }
    ]
    assert response.seeds == response.knowledge_requests
