-- =============================================================================
-- Migration: 0004_create_user_profile
-- Module   : memory
-- Purpose  : Long-term structured memory — thuộc tính ổn định của user
--            (VD: tên, ngôn ngữ ưa dùng, múi giờ, sở thích cố định...).
--            Khác episodic_memory ở chỗ: đây là key-value lookup trực tiếp,
--            KHÔNG cần semantic search / embedding — vì đã biết chính xác
--            key cần lấy khi build prompt (VD: luôn lấy "preferred_language"
--            của user, không cần "tìm" nó).
--
-- Phân biệt với episodic_memory:
--   - episodic_memory: "User đã từng phàn nàn về giao hàng chậm" → cần
--     semantic search vì không biết trước sẽ hỏi gì.
--   - user_profile: "preferred_language = vi" → biết trước key, chỉ cần
--     lookup, không cần vector.
--
-- Design notes:
--   - unique(user_id, key): mỗi user chỉ có 1 giá trị active cho mỗi key.
--     Khi value đổi (VD: user đổi ngôn ngữ ưa dùng), UPDATE trực tiếp,
--     KHÔNG giữ lịch sử (khác episodic_memory) — vì đây là "trạng thái
--     hiện tại", không phải "sự kiện có thời điểm".
--   - Nếu sau này cần audit lịch sử thay đổi profile, cân nhắc thêm bảng
--     user_profile_history riêng, không nhồi vào bảng này.
-- =============================================================================

create table if not exists user_profile (
    id            uuid primary key default gen_random_uuid(),

    user_id       uuid not null,

    key           text not null,          -- VD: 'preferred_language', 'timezone', 'communication_style'
    value         text not null,          -- lưu dạng text; parse kiểu dữ liệu cụ thể ở application layer
    value_type    text not null default 'string'
                    check (value_type in ('string', 'number', 'boolean', 'json')),

    -- Nguồn gốc: profile field này được set thủ công (user khai báo) hay
    -- được suy ra (LLM infer từ hội thoại) — quan trọng để quyết định độ
    -- tin cậy khi 2 nguồn xung đột nhau.
    source        text not null default 'inferred'
                    check (source in ('explicit', 'inferred')),

    confidence    real not null default 1.0 check (confidence between 0 and 1),

    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),

    constraint uq_user_profile_key unique (user_id, key)
);

-- Truy vấn chính: lấy toàn bộ profile của 1 user khi build prompt
create index if not exists idx_user_profile_user
    on user_profile (user_id);

comment on table user_profile is
    'Long-term structured memory: key-value thuộc tính ổn định của user, lookup trực tiếp, không cần semantic search.';
comment on column user_profile.source is
    'explicit = user tự khai báo (độ tin cậy cao hơn); inferred = LLM suy ra từ hội thoại (cần đối chiếu khi conflict).';
comment on column user_profile.confidence is
    'Dùng khi consolidate: nếu fact mới inferred có confidence thấp hơn field explicit hiện tại, có thể bỏ qua UPDATE.';