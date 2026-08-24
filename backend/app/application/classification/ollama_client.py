from __future__ import annotations

from typing import Any

from openai import (
    AsyncAzureOpenAI,
)

from app.application.classification.model_provider import (
    ModelConfig,
)


class ModelCallError(Exception):
    """Raise khi gọi model thất bại."""


async def call_model(
    model: ModelConfig,
    prompt: str,
) -> str:

    try:

        client = AsyncAzureOpenAI(
            azure_endpoint=(
                model.base_url
            ),
            api_key=(
                model.api_key
            ),
            api_version=(
                "2024-10-21"
            ),
        )

        response = await (
            client.chat.completions.create(
                model=model.name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.0,
                max_completion_tokens=200,
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if content is None:
            raise ModelCallError(
                f"Model '{model.name}' "
                f"trả về response rỗng."
            )

        return content

    except Exception as e:

        raise ModelCallError(
            f"Gọi model '{model.name}' "
            f"thất bại: {e}"
        ) from e