from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
)
from uuid import UUID


@dataclass
class Chunk:

    id: UUID

    content: str

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class EmbeddingResult:

    chunk_id: UUID

    vector: list[float] | None

    model_name: str

    dimension: int | None = None

    token_count: int | None = None

    status: str = "ok"

    error_message: str | None = None