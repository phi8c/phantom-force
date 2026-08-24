from __future__ import annotations

from dataclasses import dataclass

from app.shared.config.settings import settings


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: str
    base_url: str
    api_key: str
    max_context_tokens: int
    timeout_seconds: int = 60


def get_model_set(
    purpose: str = "classification",
) -> list[ModelConfig]:

    if purpose == "classification":

        return [
            ModelConfig(
                name="gpt-5.1",
                provider="azure_openai",
                base_url=(
                    settings.AZURE_OPENAI_ENDPOINT
                    .strip()
                ),
                api_key=(
                    settings.AZURE_OPENAI_API_KEY
                    .strip()
                ),
                max_context_tokens=128000,
                timeout_seconds=60,
            ),
        ]

    raise ValueError(
        f"Không có model set nào được "
        f"cấu hình cho purpose='{purpose}'"
    )