"""
Entity: MemoryBuffer

Ánh xạ 1:1 theo bảng `memory_buffer` (migrations/0001_create_memory_buffer.sql).
KHÔNG thêm field nào không có trong DB — nếu cần field mới, sửa migration
trước, entity này sau (đúng nguyên tắc DB-first của module).

Đây là working memory: raw message của conversation hiện tại, đọc tuần tự
theo thời gian, không qua semantic search.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID


class MessageRole(str, Enum):
    """Khớp check constraint `role in ('user','assistant','system')` ở DB."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class MemoryBuffer:
    id: UUID
    user_id: UUID
    conversation_id: UUID

    role: MessageRole
    content: str

    token_count: int = 0
    is_summarized: bool = False

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("MemoryBuffer.content không được rỗng")

        if self.token_count < 0:
            raise ValueError("MemoryBuffer.token_count không được âm")

        if isinstance(self.role, str) and not isinstance(self.role, MessageRole):
            # Cho phép khởi tạo bằng string thường (VD: từ DB row), tự convert.
            self.role = MessageRole(self.role)

    def mark_summarized(self) -> None:
        """Đánh dấu turn này đã được gộp vào session_summary.

        Lưu ý: không xoá record — chỉ đổi flag (xem lý do trong
        migrations/0001_create_memory_buffer.sql).
        """
        self.is_summarized = True