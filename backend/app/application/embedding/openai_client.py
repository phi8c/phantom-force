from __future__ import annotations

import time

import requests

from app.application.embedding.model_provider import (
    EmbeddingModelConfig,
)


_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 2


class EmbeddingCallError(Exception):
    """Raise khi gọi embedding API thất bại sau khi đã retry."""


def call_embedding_api(
    model: EmbeddingModelConfig,
    texts: list[str],
) -> list[list[float]]:

    if not texts:
        return []

    url = (
        f"{model.base_url.rstrip('/')}"
        f"/openai/deployments/"
        f"{model.name}"
        f"/embeddings"
        f"?api-version=2024-10-21"
    )

    headers = {
        "api-key": model.api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "input": texts,
    }

    last_error: Exception | None = None

    for attempt in range(
        1,
        _MAX_RETRIES + 1,
    ):

        try:

            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=model.timeout_seconds,
            )

            resp.raise_for_status()

            data = resp.json()

            items = data.get("data")

            if items is None:

                raise EmbeddingCallError(
                    "Response không hợp lệ từ "
                    f"Azure OpenAI: {data}"
                )

            items_sorted = sorted(
                items,
                key=lambda item: item["index"],
            )

            return [
                item["embedding"]
                for item in items_sorted
            ]

        except requests.RequestException as e:

            last_error = e

            print(
                f"Azure Embedding attempt "
                f"{attempt}/{_MAX_RETRIES} failed: "
                f"{e}"
            )

            if attempt < _MAX_RETRIES:

                sleep_seconds = (
                    _BACKOFF_BASE_SECONDS
                    ** attempt
                )

                time.sleep(
                    sleep_seconds,
                )

                continue

    raise EmbeddingCallError(
        f"Gọi Azure OpenAI embedding "
        f"'{model.name}' thất bại sau "
        f"{_MAX_RETRIES} lần thử: "
        f"{last_error}"
    ) from last_error