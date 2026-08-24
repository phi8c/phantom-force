-- =============================================================================
-- Migration: 0002_create_episodic_memory
-- Module   : memory
-- Purpose  : Long-term episodic memory — các "fact" đã được LLM extract từ
--            conversation, có embedding để semantic search, và có thời hạn
--            hiệu lực (temporal) để hỗ trợ trường hợp fact bị thay đổi theo
--            thời gian (kiểu Zep: không xoá fact cũ, chỉ đóng valid_until).
--
-- Pipeline liên quan: application/use_cases/consolidate_memory.py sẽ quyết
--            định ADD / UPDATE / DELETE / NOOP dựa trên so sánh semantic
--            similarity với các record đang active (valid_until is null).
--
-- Design notes:
--   - Không FK cứng tới users/conversations (giống 0001).
--   - source_turn_id trỏ về memory_buffer.id (cùng module) — giữ để audit
--     "fact này được extract từ turn nào".
--   - Vector dimension = 1536, khớp OpenAI text-embedding-3-small.
--     Nếu đổi embedding model sau này (dimension khác) → cần migration mới,
--     KHÔNG sửa trực tiếp cột này (xem README.md trong migrations/).
-- =============================================================================

create extension if not exists vector;

create table if not exists episodic_memory (
    id                uuid primary key default gen_random_uuid(),

    user_id           uuid not null,
    conversation_id   uuid, -- có thể null: fact có thể không gắn với 1 conversation cụ thể (cross-session)

    -- Liên kết nội bộ module: fact này được extract từ turn nào trong buffer
    source_turn_id    uuid references memory_buffer(id) on delete set null,

    content           text not null,           -- nội dung fact dạng câu, VD: "User thích cà phê đen không đường"
    embedding         vector(1536) not null,    -- text-embedding-3-small

    memory_type       text not null default 'episodic'
                        check (memory_type in ('episodic', 'preference', 'decision', 'event')),

    importance_score  real not null default 0.5 check (importance_score between 0 and 1),

    -- Temporal validity kiểu Zep: fact cũ không bị xoá khi bị thay thế,
    -- chỉ đóng valid_until. valid_until = null nghĩa là đang "active".
    valid_from        timestamptz not null default now(),
    valid_until       timestamptz,

    -- Khi 1 fact bị UPDATE, record mới trỏ về record cũ nó thay thế —
    -- phục vụ truy vết lịch sử thay đổi của 1 fact theo thời gian.
    superseded_by      uuid references episodic_memory(id) on delete set null,

    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

-- Semantic search: chỉ tìm trong các fact đang active (valid_until is null)
create index if not exists idx_episodic_memory_embedding_hnsw
    on episodic_memory using hnsw (embedding vector_cosine_ops)
    where valid_until is null;

-- Lookup theo user, chỉ fact active — dùng kết hợp với semantic search ở application layer
create index if not exists idx_episodic_memory_user_active
    on episodic_memory (user_id)
    where valid_until is null;

-- Phục vụ prune_job: tìm fact hết hạn hoặc importance thấp
create index if not exists idx_episodic_memory_importance
    on episodic_memory (importance_score);

comment on table episodic_memory is
    'Long-term episodic memory: fact đã extract, có embedding, hỗ trợ temporal supersession (không xoá fact cũ khi update).';
comment on column episodic_memory.valid_until is
    'null = fact đang active. Khi bị thay thế bởi fact mới, set thời điểm supersede, không xoá row.';
comment on column episodic_memory.superseded_by is
    'Trỏ tới record mới thay thế fact này (nếu có) — dùng để truy vết lịch sử thay đổi.';
comment on column episodic_memory.importance_score is
    'Dùng trong retrieval_score (application layer): score = w1*semantic + w2*recency_decay + w3*importance.';