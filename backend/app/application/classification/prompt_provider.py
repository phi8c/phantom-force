"""
PromptProvider - GIẢ LẬP (hardcode) cho tới khi module Prompt thật được xây dựng.

Sau này module Prompt sẽ quản lý nhiều loại prompt cho nhiều mục đích khác
nhau, seed sẵn trong DB và load ra theo điều kiện (vd purpose="classification",
version="latest", locale="vi"...). Hiện tại engine chỉ dùng 1 template cố định
để luồng chạy được trước.
"""

from __future__ import annotations

from app.application.classification.schemas import (
    Chunk,
)

# TODO(prompt-module):
# Khi module Prompt được xây dựng, hàm get_prompt_template()
# sẽ query DB (bảng prompt, filter theo purpose + version đang active)
# thay vì trả string hardcode như bên dưới.
_CLASSIFICATION_PROMPT_TEMPLATE = """Bạn là hệ thống phân loại nội dung tài liệu.

Dưới đây là danh sách các đoạn văn bản (chunk), mỗi đoạn có id riêng.

Với MỖI chunk, hãy xác định nhãn phân loại (label) phù hợp nhất.

Chỉ trả lời bằng JSON, đúng định dạng sau.
Không thêm markdown.
Không thêm giải thích.
Không thêm bất kỳ nội dung nào khác.

[
  {{
    "chunk_id": "<id>",
    "label": "<nhãn>",
    "confidence": <0-1>
  }}
]

Danh sách chunk:

{chunks_block}
"""


def get_prompt_template(
    purpose: str = "classification",
) -> str:

    if purpose == "classification":
        return _CLASSIFICATION_PROMPT_TEMPLATE

    raise ValueError(
        f"Không có prompt cho purpose='{purpose}'."
    )


def build_chunks_block(
    chunks: list[Chunk],
) -> str:
    """
    Chuyển danh sách Chunk thành block text đưa vào prompt.

    UUID chỉ được convert sang string tại đây vì đây là ranh giới
    giao tiếp với LLM.
    """

    return "\n\n".join(
        [
            (
                f"--- chunk_id: {str(chunk.id)} ---\n"
                f"{chunk.content}"
            )
            for chunk in chunks
        ]
    )


def build_prompt(
    chunks: list[Chunk],
    purpose: str = "classification",
) -> str:

    template = get_prompt_template(
        purpose,
    )

    chunks_block = build_chunks_block(
        chunks,
    )

    return template.format(
        chunks_block=chunks_block,
    )