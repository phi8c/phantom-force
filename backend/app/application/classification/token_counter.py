"""
Đếm / ước lượng số token của 1 đoạn text.

Model local qua Ollama không có API đếm token tiện lợi như OpenAI, nên ở đây
dùng công thức ước lượng xấp xỉ theo số ký tự. Hệ số CHARS_PER_TOKEN_ESTIMATE
được set thiên về an toàn (ước lượng cao hơn thực tế 1 chút) để tránh việc
build prompt vượt quá context window thật của model.

Nếu sau này cần chính xác hơn, có thể thay bằng tokenizer thật của model
đang dùng (ví dụ dùng thư viện tokenizer riêng của Gemma).
"""
from __future__ import annotations

from app.application.classification.schemas import Chunk

_CHARS_PER_TOKEN_ESTIMATE = 3.2  # hệ số an toàn, có thể tinh chỉnh lại sau


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / _CHARS_PER_TOKEN_ESTIMATE))


def estimate_tokens_for_chunks(chunks: list[Chunk]) -> int:
    return sum(estimate_tokens(c.content) for c in chunks)