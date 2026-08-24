-- =============================================================================
-- Migration: 0001_create_memory_buffer
-- Module   : memory
-- Purpose  : Working memory (short-term) — lưu raw message của conversation
--            hiện tại, dùng để build context ngay lập tức, không cần retrieval.
--
-- Lifecycle: buffer sẽ được đọc tuần tự theo conversation_id, khi vượt ngưỡng
--            token (config ở application layer) sẽ bị "summarize" và đánh dấu
--            is_summarized = true (không xoá ngay — giữ để audit/debug/re-process).
--
-- Design notes:
--   - Không đặt FK cứng tới bảng users/conversations của module khác (chat),
--     để giữ migration của memory module độc lập, chạy được riêng biệt.
--   - Ràng buộc toàn vẹn (user tồn tại, conversation tồn tại) xử lý ở
--     application layer, không ở DB layer.
-- =============================================================================

create table if not exists memory_buffer (
    id              uuid primary key default gen_random_uuid(),

    -- Soft reference tới module khác — không FK cứng (xem design notes)
    user_id         uuid not null,
    conversation_id uuid not null,

    role            text not null check (role in ('user', 'assistant', 'system')),
    content         text not null,

    -- Token count được tính sẵn khi insert (application layer), tránh phải
    -- tokenize lại mỗi lần check ngưỡng summarize.
    token_count     integer not null default 0,

    -- Đánh dấu khi turn này đã được gộp vào session_summary.
    -- Buffer KHÔNG bị xoá sau khi summarize — chỉ đánh dấu, phục vụ audit
    -- và cho phép re-summarize nếu đổi model/prompt sau này.
    is_summarized   boolean not null default false,

    created_at      timestamptz not null default now()
);

-- Truy vấn phổ biến nhất: lấy N turn gần nhất của 1 conversation, theo thời gian
create index if not exists idx_memory_buffer_conversation_created
    on memory_buffer (conversation_id, created_at desc);

-- Phục vụ prune job / thống kê theo user
create index if not exists idx_memory_buffer_user
    on memory_buffer (user_id);

-- Phục vụ job summarize: quét các turn chưa được summarize theo conversation
create index if not exists idx_memory_buffer_unsummarized
    on memory_buffer (conversation_id, is_summarized)
    where is_summarized = false;

comment on table memory_buffer is
    'Working memory (short-term): raw message buffer theo conversation, chờ được summarize khi vượt ngưỡng token.';
comment on column memory_buffer.token_count is
    'Tính sẵn ở application layer lúc insert, dùng để tổng hợp nhanh khi check ngưỡng trigger summarize.';
comment on column memory_buffer.is_summarized is
    'true khi turn đã được gộp vào session_summary. Không xoá row để giữ khả năng audit/re-process.';