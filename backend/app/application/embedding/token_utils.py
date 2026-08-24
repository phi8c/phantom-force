"""
Truncate text sao cho vừa với max_tokens, dựa trên TokenCounter contract
có sẵn của dự án (app/application/chunking/contracts/token_counter.py).

Vì TokenCounter chỉ expose `count()` (không có encode/decode), ở đây dùng
binary search trên số ký tự để tìm điểm cắt phù hợp - không tối ưu bằng cắt
trực tiếp theo token id, nhưng không cần thêm dependency và đủ chính xác vì
chỉ chạy khi 1 chunk vượt giới hạn (trường hợp hiếm).
"""
from __future__ import annotations

from app.application.chunking.contracts.token_counter import (
    TokenCounter,
)


def truncate_to_max_tokens(
    text: str,
    token_counter: TokenCounter,
    max_tokens: int,
) -> str:
    if token_counter.count(text) <= max_tokens:
        return text

    low, high = 0, len(text)
    best = ""

    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid]

        if token_counter.count(candidate) <= max_tokens:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1

    return best