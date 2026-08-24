# Migrations — module `memory`

## Quy ước đặt tên
```
NNNN_verb_noun.sql
```
- `NNNN`: số thứ tự 4 chữ số, tăng dần, **không** đánh lại số khi rollback (xem bên dưới).
- `verb`: `create` / `alter` / `drop` / `add` / `backfill`...
- Ví dụ: `0005_add_metadata_to_episodic_memory.sql`

## Thứ tự chạy hiện tại
| # | File | Phụ thuộc |
|---|------|-----------|
| 0001 | `create_memory_buffer` | không có |
| 0002 | `create_episodic_memory` | 0001 (FK `source_turn_id` → `memory_buffer.id`) |
| 0003 | `create_session_summary` | không phụ thuộc bảng khác trong module |
| 0004 | `create_user_profile` | không phụ thuộc bảng khác trong module |
| 0005 | `add_iam_users_fk` | 0001-0004 trong module này, **và module `iam` phải migrate trước** (ALTER, thêm FK `user_id` → `iam.users(id)`) |

Chạy tuần tự theo số thứ tự. Không skip, không đổi thứ tự.

## Nguyên tắc DB-first của module này
- SQL trong `migrations/` là **nguồn sự thật duy nhất** về schema.
- `domain/entities/` chỉ được viết/sửa **sau khi** migration đã chạy — entity ánh xạ theo DB, không sinh ngược.
- Khi cần đổi schema: viết migration mới (không sửa lại file cũ đã chạy ở môi trường khác), rồi mới cập nhật entity tương ứng.

## Rollback
- Mỗi migration file `NNNN_*.sql` nên có file `NNNN_*.down.sql` tương ứng nếu thay đổi có nguy cơ mất dữ liệu (drop column, drop table). Hiện tại 4 migration đầu đều là `create table` nên rollback đơn giản là `drop table if exists <table_name>;` — chưa cần file `.down.sql` riêng, nhưng bắt buộc thêm khi có `alter`/`drop` sau này.
- Không rollback trên production nếu đã có dữ liệu ghi vào bảng — ưu tiên viết migration mới để sửa/bù thay vì lùi lại.

## Lưu ý về FK `user_id -> iam.users(id)` (0005)
- Đây là **ngoại lệ có chủ đích** với nguyên tắc "không FK cứng cross-module": `iam.users` là bảng do module `iam` của chính dự án tạo — chấp nhận coupling này vì `iam` gần như chắc chắn là module nền tảng, migrate đầu tiên trong mọi trường hợp.
- **Dependency tường minh**: migration 0005 của `memory` chỉ chạy được sau khi module `iam` đã migrate (bảng `iam.users`, enum `iam.user_status` phải tồn tại trước).
- `conversation_id` vẫn giữ nguyên **không FK** vì đó là bảng thuộc module `chat` — module ngang hàng, không phải nền tảng như `iam`.
- **Soft-delete**: `iam.users` dùng `deleted_at`, không hard-delete. `ON DELETE CASCADE` ở migration này chỉ là lưới an toàn cho hard-delete hiếm gặp — dọn memory khi soft-delete phải xử lý riêng ở `infrastructure/jobs/prune_job.py`.

## Lưu ý riêng cho `episodic_memory` (0002)
- Cột `embedding vector(1536)` khớp `text-embedding-3-small`. Đổi embedding model (khác dimension) **không** sửa trực tiếp cột này — phải tạo bảng/cột mới, vì index HNSW đã build theo dimension cũ.