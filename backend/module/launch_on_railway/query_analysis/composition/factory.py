from module.ai.llm.composition import LLMGateway
from module.prompt.composition import PromptProvider

from module.launch_on_railway.query_analysis.application.services.query_analyzer import (
    QueryAnalyzer,
)


def create_query_analyzer(
    prompt_provider: PromptProvider,
    llm_gateway: LLMGateway,
) -> QueryAnalyzer:
    return QueryAnalyzer(
        prompt_provider=prompt_provider,
        llm_gateway=llm_gateway,
    )