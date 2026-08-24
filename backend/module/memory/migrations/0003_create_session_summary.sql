-- =============================================================================
-- Migration: 0003_create_session_summary
-- Module   : memory
-- Purpose  : Mid-term memory — rolling summary của 1 conversation, được cập
--            nhật dần khi memory_buffer vượt ngưỡng token (application layer
--            quyết định ngưỡng, xem config/settings.py).
--
-- Lifecycle: Mỗi conversation chỉ có 1 record active. Khi buffer mới đủ
--            ngưỡng để summarize tiếp, use case summarize_session sẽ:
--              1) Lấy summary hiện tại (nếu có) + các turn mới trong
--                 memory_buffer chưa được cover (created_at > covered_until)
--              2) Gọi LLM gộp thành summary mới
--              3) UPDATE record này (không insert mới) → tăng version
--
-- Design notes:
--   - Không FK cứng tới users/conversations (giống 0001, 0002).
--   - unique(conversation_id) vì mỗi conversation chỉ có 1 summary active —
--     ép ràng buộc "rolling" ngay ở DB level, tránh bug insert trùng.
--   - Có embedding riêng (không dùng chung với episodic_memory) vì summary
--     là 1 loại nội dung khác: tổng quan cả đoạn hội thoại, không phải
--     1 fact rời rạc — cần semantic search độc lập khi retrieval cần ngữ
--     cảnh tổng thể thay vì từng fact.
-- =============================================================================

create table if not exists session_summary (
    id                uuid primary key default gen_random_uuid(),

    user_id           uuid not null,
    conversation_id   uuid not null,

    content           text not null,           -- bản tóm tắt hiện tại (rolling)
    embedding         vector(1536),             -- text-embedding-3-small, nullable: có thể chưa embed ngay

    -- Đánh dấu summary này đã cover buffer tới thời điểm nào.
    -- summarize_session dùng field này để biết nên lấy buffer từ đâu tiếp.
    covered_until     timestamptz not null,

    -- Số lần đã được update/rolling — phục vụ debug, theo dõi độ "trôi"
    -- của summary qua nhiều lần gộp.
    version           integer not null default 1,

    token_count       integer not null default 0,

    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),

    constraint uq_session_summary_conversation unique (conversation_id)
);

-- Lookup theo conversation — truy vấn phổ biến nhất (lấy summary hiện tại)
create index if not exists idx_session_summary_conversation
    on session_summary (conversation_id);

-- Lookup theo user — khi cần liệt kê summary của tất cả conversation của 1 user
create index if not exists idx_session_summary_user
    on session_summary (user_id);

-- Semantic search trên summary (khi retrieval cần ngữ cảnh tổng thể)
create index if not exists idx_session_summary_embedding_hnsw
    on session_summary using hnsw (embedding vector_cosine_ops)
    where embedding is not null;

comment on table session_summary is
    'Mid-term memory: rolling summary của 1 conversation, update liên tục thay vì tạo record mới mỗi lần summarize.';
comment on column session_summary.covered_until is
    'Thời điểm buffer đã được cover bởi summary này — dùng để xác định buffer nào cần gộp tiếp.';
comment on column session_summary.version is
    'Tăng mỗi lần rolling-update, không phải để versioning phục vụ rollback — chỉ để observability.';