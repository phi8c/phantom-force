from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class Chunk:
    """Một chunk văn bản được tạo ra từ luồng ingest."""

    id: UUID

    content: str

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """Kết quả phân loại cho 1 chunk."""

    chunk_id: UUID

    label: str

    confidence: float | None = None

    raw_response: str | None = None
    
    model_name: str | None = None