from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.knowledge_selection.application.services.knowledge_selector import (
    KnowledgeSelector,
)


def create_knowledge_selector(
    prompt_provider: PromptProvider,
    llm_gateway: LLMGateway,
) -> KnowledgeSelector:
    return KnowledgeSelector(
        prompt_provider=prompt_provider,
        llm_gateway=llm_gateway,
    )
