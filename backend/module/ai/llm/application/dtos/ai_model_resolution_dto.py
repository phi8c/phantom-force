from dataclasses import dataclass

from module.ai.llm.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.llm.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)


@dataclass
class AIModelResolutionDTO:

    provider: AIProviderDTO

    model: AIModelDTO
