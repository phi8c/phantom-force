from typing import Any

from module.ai.llm.application.services.ai_model_provider import (
    AIModelProvider,
)
from module.ai.llm.domain.contracts.llm_gateway import (
    LLMGateway,
)
from module.ai.llm.domain.value_objects.llm_result import (
    LLMResult,
)


class AzureOpenAILLMGateway(
    LLMGateway,
):

    def __init__(
        self,
        ai_model_provider: AIModelProvider,
        client: Any | None = None,
    ):
        self._ai_model_provider = ai_model_provider
        self._client = client

    async def generate(
        self,
        provider_code: str,
        model_code: str,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> LLMResult:

        resolved_model = await self._ai_model_provider.get(
            provider_code=provider_code,
            model_code=model_code,
        )

        if resolved_model is None:
            raise ValueError(
                "AI provider/model not found or disabled",
            )

        provider = resolved_model.provider
        model = resolved_model.model

        client = self._get_client(
            base_url=provider.base_url,
            api_version=provider.api_version,
        )

        request_config = dict(
            config or {},
        )
        deployment = request_config.pop(
            "deployment",
            model.code,
        )

        request = {
            "model": deployment,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            **request_config,
        }

        if response_format is not None:
            request["response_format"] = response_format

        response = await client.chat.completions.create(
            **request,
        )

        choice = response.choices[0]

        return LLMResult(
            content=choice.message.content,
            provider_code=provider.code,
            model_code=model.code,
            response_id=getattr(
                response,
                "id",
                None,
            ),
            finish_reason=getattr(
                choice,
                "finish_reason",
                None,
            ),
            usage=self._usage_to_dict(
                getattr(
                    response,
                    "usage",
                    None,
                ),
            ),
        )

    def _get_client(
        self,
        base_url: str | None,
        api_version: str | None,
    ):

        if self._client is not None:
            return self._client

        from openai import AsyncAzureOpenAI

        from shared.config.settings import settings

        self._client = AsyncAzureOpenAI(
            azure_endpoint=(
                base_url
                or settings.AZURE_OPENAI_ENDPOINT
            ),
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=(
                api_version
                or settings.AZURE_OPENAI_API_VERSION
            ),
        )

        return self._client

    @staticmethod
    def _usage_to_dict(
        usage,
    ) -> dict[str, Any]:

        if usage is None:
            return {}

        if hasattr(
            usage,
            "model_dump",
        ):
            return usage.model_dump()

        return {
            "prompt_tokens": getattr(
                usage,
                "prompt_tokens",
                None,
            ),
            "completion_tokens": getattr(
                usage,
                "completion_tokens",
                None,
            ),
            "total_tokens": getattr(
                usage,
                "total_tokens",
                None,
            ),
        }
