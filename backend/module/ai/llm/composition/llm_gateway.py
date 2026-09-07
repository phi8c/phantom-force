from typing import Any

from module.ai.llm.domain.contracts.llm_gateway import (
    LLMGateway as DomainLLMGateway,
)
from module.ai.llm.domain.value_objects.llm_result import (
    LLMResult,
)


class LLMGateway:

    def __init__(
        self,
        gateway: DomainLLMGateway,
    ):
        self._gateway = gateway

    async def generate(
        self,
        provider_code: str,
        model_code: str,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> LLMResult:

        return await self._gateway.generate(
            provider_code=provider_code,
            model_code=model_code,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=response_format,
            config=config,
        )
