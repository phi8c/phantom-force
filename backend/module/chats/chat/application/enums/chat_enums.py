from enum import Enum


class ChatPromptCode(Enum):
    ANSWER_GENERATION = (
        "launch_on_railway.answer_generation"
    )


class ChatProviderCode(Enum):
    AZURE_OPENAI = "azure_openai"


class ChatModelCode(Enum):
    ANSWER_GENERATION = "gpt-5.1"