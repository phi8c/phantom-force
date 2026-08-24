from __future__ import annotations

from dataclasses import dataclass

from app.shared.config.settings import settings


@dataclass(frozen=True)
class EmbeddingModelConfig:
    name: str
    provider: str
    api_key: str
    base_url: str
    max_input_tokens: int
    dimension: int
    timeout_seconds: int = 60


def get_embedding_model(
    purpose: str = "embedding",
) -> EmbeddingModelConfig:

    if purpose == "embedding":

        return EmbeddingModelConfig(
            name="text-embedding-3-small",
            provider="azure_openai",
            api_key=(
                settings.AZURE_OPENAI_API_KEY
                .strip()
            ),
            base_url=(
                settings.AZURE_OPENAI_ENDPOINT
                .strip()
            ),
            max_input_tokens=8191,
            dimension=1536,
            timeout_seconds=60,
        )

    raise ValueError(
        f"Không có model embedding nào được "
        f"cấu hình cho purpose='{purpose}'"
    )