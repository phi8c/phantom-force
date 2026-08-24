-- =============================================================================
-- Migration: 0005_add_iam_users_fk
-- Module   : memory
-- Purpose  : Thêm FK `user_id -> iam.users(id)` cho cả 4 bảng của module.
--
-- ⚠️ LƯU Ý QUAN TRỌNG VỀ CROSS-MODULE DEPENDENCY:
--   Khác với giả định ban đầu (Supabase Auth `auth.users` — hạ tầng nền
--   tảng có sẵn), dự án này dùng bảng `iam.users` tự viết, thuộc module
--   `iam` riêng của chính dự án. Migration này VÌ VẬY tạo ra 1 dependency
--   tường minh: migration 0005 của module `memory` chỉ chạy được SAU KHI
--   module `iam` đã migrate xong (bảng iam.users, schema iam.user_status
--   đã tồn tại).
--
--   Đây là ngoại lệ có chủ đích với nguyên tắc "không FK cứng cross-module"
--   đã thống nhất trước đó — chấp nhận vì `iam` gần như chắc chắn là module
--   nền tảng, migrate đầu tiên trong mọi dự án, rủi ro đảo thứ tự gần như
--   bằng 0 (khác hẳn `chat`, vẫn giữ nguyên KHÔNG FK vì là module ngang hàng
--   có thể đổi cấu trúc/tách rời sau này).
--
-- ⚠️ LƯU Ý VỀ SOFT-DELETE:
--   iam.users dùng soft-delete (cột deleted_at), KHÔNG hard-delete trong
--   vận hành bình thường. Do đó `ON DELETE CASCADE` dưới đây gần như KHÔNG
--   BAO GIỜ tự kích hoạt — nó chỉ là lưới an toàn cho trường hợp hard-delete
--   thật sự (hiếm, VD: admin xoá cứng theo yêu cầu GDPR).
--
--   Việc dọn dẹp memory khi user bị SOFT-DELETE (deleted_at IS NOT NULL)
--   PHẢI được xử lý riêng ở application layer — cụ thể là
--   infrastructure/jobs/prune_job.py cần quét thêm điều kiện:
--     "user_id thuộc về iam.users có deleted_at IS NOT NULL" → prune.
--   FK cascade ở migration này KHÔNG thay thế được logic đó.
-- =============================================================================

alter table memory_buffer
    add constraint fk_memory_buffer_user
    foreign key (user_id) references iam.users(id)
    on delete cascade;

alter table episodic_memory
    add constraint fk_episodic_memory_user
    foreign key (user_id) references iam.users(id)
    on delete cascade;

alter table session_summary
    add constraint fk_session_summary_user
    foreign key (user_id) references iam.users(id)
    on delete cascade;

alter table user_profile
    add constraint fk_user_profile_user
    foreign key (user_id) references iam.users(id)
    on delete cascade;

comment on constraint fk_memory_buffer_user on memory_buffer is
    'Tham chiếu tới module iam (iam.users) — cross-module FK có chủ đích, xem design notes trong file migration.';