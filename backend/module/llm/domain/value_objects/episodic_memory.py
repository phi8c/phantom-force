"""
Entity: EpisodicMemory

Ánh xạ 1:1 theo bảng `episodic_memory` (migrations/0002_create_episodic_memory.sql).

Long-term memory: fact đã được LLM extract, có embedding, hỗ trợ temporal
supersession kiểu Zep — fact cũ không bị xoá khi bị thay thế, chỉ đóng
`valid_until` và trỏ `superseded_by` sang record mới.

Lưu ý phân biệt EpisodicMemoryKind (enum dưới đây) với MemoryType trong
domain/value_objects/memory_type.py:
  - MemoryType (value_objects)  : phân loại theo TẦNG memory (WORKING / MID /
    LONG_TERM_EPISODIC / LONG_TERM_PROFILE) — dùng xuyên suốt module, kể cả
    ở retrieval/port layer khi cần biết đang thao tác với tầng nào.
  - EpisodicMemoryKind (ở đây)  : phân loại NỘI DUNG bên trong tầng episodic
    (một fact là loại preference, decision, hay event) — chỉ có ý nghĩa
    trong phạm vi bảng episodic_memory, khớp check constraint `memory_type`
    của chính bảng này.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

EMBEDDING_DIM = 1536  # text-embedding-3-small — khớp migration 0002


class EpisodicMemoryKind(str, Enum):
    """Khớp check constraint `memory_type` của bảng episodic_memory."""

    EPISODIC = "episodic"
    PREFERENCE = "preference"
    DECISION = "decision"
    EVENT = "event"


@dataclass
class EpisodicMemory:
    id: UUID
    user_id: UUID

    content: str
    embedding: list[float]

    conversation_id: UUID | None = None
    source_turn_id: UUID | None = None

    memory_type: EpisodicMemoryKind = EpisodicMemoryKind.EPISODIC
    importance_score: float = 0.5

    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    superseded_by: UUID | None = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("EpisodicMemory.content không được rỗng")

        if len(self.embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"EpisodicMemory.embedding phải có {EMBEDDING_DIM} chiều, "
                f"nhận {len(self.embedding)}"
            )

        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("EpisodicMemory.importance_score phải trong [0, 1]")

        if isinstance(self.memory_type, str) and not isinstance(
            self.memory_type, EpisodicMemoryKind
        ):
            self.memory_type = EpisodicMemoryKind(self.memory_type)

        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("valid_until phải muộn hơn valid_from")

    @property
    def is_active(self) -> bool:
        """True nếu fact chưa bị supersede (valid_until is null ở DB)."""
        return self.valid_until is None

    def supersede(self, replacement_id: UUID, at: datetime | None = None) -> None:
        """Đóng hiệu lực fact này vì đã có fact mới thay thế.

        Gọi từ use case `consolidate_memory` khi quyết định UPDATE — record
        cũ (self) bị đóng, record mới được tạo riêng (không sửa content của
        record cũ), giữ nguyên lịch sử theo đúng thiết kế temporal ở 0002.
        """
        if not self.is_active:
            raise ValueError("Fact này đã bị supersede trước đó, không thể supersede lần nữa")

        self.valid_until = at or datetime.now(timezone.utc)
        self.superseded_by = replacement_id
        self.updated_at = self.valid_until