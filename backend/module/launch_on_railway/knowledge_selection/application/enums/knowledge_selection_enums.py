from enum import Enum


class KnowledgeSelectionPromptCode(Enum):
    SELECT_KNOWLEDGE = (
        "launch_on_railway.knowledge_selection"
    )


class KnowledgeSelectionProviderCode(Enum):
    AZURE_OPENAI = "azure_openai"


class KnowledgeSelectionModelCode(Enum):
    SELECT_KNOWLEDGE = "gpt-5.1"
