from abc import ABC
from abc import abstractmethod
from typing import Any

from module.ai.llm.domain.value_objects.llm_result import (
    LLMResult,
)


class LLMGateway(
    ABC,
):

    @abstractmethod
    async def generate(
        self,
        provider_code: str,
        model_code: str,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> LLMResult:
        pass
