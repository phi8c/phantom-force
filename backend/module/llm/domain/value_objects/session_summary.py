"""
Entity: SessionSummary

Ánh xạ 1:1 theo bảng `session_summary` (migrations/0003_create_session_summary.sql).

Mid-term memory: rolling summary của 1 conversation. Mỗi conversation chỉ
có 1 record active (unique constraint ở DB) — entity này đại diện cho
record đó tại 1 thời điểm, không phải danh sách lịch sử.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class SessionSummary:
    id: UUID
    user_id: UUID
    conversation_id: UUID

    content: str
    covered_until: datetime

    embedding: list[float] | None = None
    version: int = 1
    token_count: int = 0

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("SessionSummary.content không được rỗng")

        if self.embedding is not None and len(self.embedding) != 1536:
            # Khớp dimension text-embedding-3-small đã set trong migration 0003.
            raise ValueError(
                f"SessionSummary.embedding phải có 1536 chiều, nhận {len(self.embedding)}"
            )

        if self.version < 1:
            raise ValueError("SessionSummary.version phải >= 1")

    def apply_rolling_update(self, new_content: str, new_covered_until: datetime) -> None:
        """Gộp summary mới vào record hiện tại (rolling update, không tạo record mới).

        Use case `summarize_session` sẽ gọi method này sau khi LLM sinh ra
        bản tóm tắt mới từ (summary cũ + buffer chưa cover).
        """
        if new_covered_until <= self.covered_until:
            raise ValueError(
                "new_covered_until phải muộn hơn covered_until hiện tại — "
                "tránh rolling update lùi thời gian"
            )

        self.content = new_content
        self.covered_until = new_covered_until
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        # embedding sẽ được re-embed ở application layer sau khi content đổi,
        # entity không tự tính embedding (đó là việc của EmbeddingPort).
        self.embedding = None