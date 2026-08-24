Chốt lại toàn bộ trước khi vào code, để cả hai cùng chung 1 hình dung.

## Luồng xử lý (Pipeline)

```text
User Question
     │
     ▼
1. Query Processing (1 LLM call)
   → rewrite + intent + metadata_hint
     │
     ▼
2. Access Control Filter
   → lấy permission user từ Supabase → build filter OData
     │
     ▼
3. Azure AI Search — Hybrid Query
   → vector + keyword (BM25) + filter, RRF tự động
     │
     ▼
4. Semantic Ranker (nếu index đã bật) — rerank top-k
     │
     ▼
5. Context Builder
   → merge chunk liền kề (theo chunk_index) + dedupe + order
     │
     ▼
6. Final Context → LLM trả lời
     │
     ▼
7. Log lại vào Supabase (retrieval_logs) để debug/eval sau này
```

**Không làm ở bản này**: Query Decomposition, Context Evaluation, Iterative Retrieval — thêm sau khi có data thật từ `retrieval_logs`.

## Cấu trúc thư mục (Clean Architecture)

```
retrieval/
│
├── domain/
│   ├── entities/
│   │   ├── chunk.py
│   │   ├── retrieval_query.py
│   │   └── retrieval_result.py
│   │
│   ├── value_objects/
│   │   ├── sensitivity_level.py
│   │   └── search_filter.py
│   │
│   └── ports/
│       ├── query_processor_port.py
│       ├── search_retriever_port.py
│       ├── reranker_port.py
│       └── permission_repository_port.py     # NEW — lấy quyền user từ Supabase
│
├── application/
│   ├── use_cases/
│   │   ├── retrieve_context_use_case.py
│   │   └── build_context_use_case.py
│   └── dto/
│       ├── retrieve_request_dto.py
│       └── retrieve_response_dto.py
│
├── infrastructure/
│   ├── azure_search/
│   │   ├── azure_search_retriever.py
│   │   ├── azure_semantic_reranker.py
│   │   └── azure_search_client.py
│   │
│   ├── llm/
│   │   ├── openai_query_processor.py
│   │   └── openai_client.py
│   │
│   ├── supabase/
│   │   ├── supabase_client.py
│   │   ├── permission_repository.py          # implement permission_repository_port
│   │   └── retrieval_log_repository.py       # ghi log vào bảng retrieval_logs
│   │
│   └── access_control/
│       └── sensitivity_filter_builder.py
│
├── interface/
│   └── api/
│       ├── retrieval_router.py
│       └── schemas/
│           └── retrieve_schema.py
│
├── config/
│   ├── settings.py
│   └── retrieval_config.py
│
└── tests/
    ├── unit/
    └── integration/
```

## Bảng cần trong Supabase

```sql
-- Đụng bảng nào cần mới tạo, còn lại giả định bạn đã có users/auth sẵn (Supabase Auth)

-- 1. Quyền truy cập — nếu chưa có
create table if not exists user_permissions (
    user_id uuid primary key references auth.users(id),
    sensitivity_max_level int not null default 1,
    allowed_departments text[] default '{}',
    updated_at timestamptz default now()
);

-- 2. Log retrieval — để debug + eval sau này
create table if not exists retrieval_logs (
    id uuid primary key default gen_random_uuid(),
    message_id uuid,              -- link tới bảng messages nếu có
    user_id uuid references auth.users(id),
    raw_question text not null,
    rewritten_query text,
    intent text,
    filters_applied jsonb,
    chunks_retrieved jsonb,       -- [{chunk_id, score}, ...]
    chunks_used_final jsonb,      -- sau rerank + context builder
    latency_ms int,
    created_at timestamptz default now()
);
```

Nếu bảng `messages`/`conversations` đã có sẵn trong source cũ thì bỏ qua, chỉ cần thêm cột `retrieval_log_id` (uuid, nullable) vào bảng `messages` để link.

## Xác nhận trước khi code file đầu tiên

Vì source đã làm lâu rồi, mình cần biết trước khi viết code để khớp đúng conventions hiện có, tránh code xong phải sửa lại:

1. Bảng `users`/`messages`/`conversations` hiện tại đặt tên và có cột gì rồi (paste schema hoặc mô tả nhanh)?
2. Stack code hiện tại: Python (FastAPI) hay Node/TS? Sync hay async?
3. Bắt đầu code từ layer nào trước — `domain` (entities/ports) hay đi thẳng vào `infrastructure/azure_search` (phần quan trọng nhất, ảnh hưởng chất lượng nhiều nhất)?




module/user/
├── facade/                                    # ⭐ CỬA DUY NHẤT — module khác CHỈ import từ đây
│   ├── contract.py                            # UserModuleFacade (ABC) — hợp đồng công khai module này cung cấp
│   ├── dto.py                                 # DTO trả ra ngoài — KHÔNG bao giờ để lọt domain Entity ra khỏi module
│   ├── local_facade.py                        # impl gọi thẳng use case, cùng process (monolith)
│   ├── http_facade.py                         # impl gọi qua HTTP client (module này đã tách microservice)
│   └── factory.py                             # chọn Local/Http theo config, module khác chỉ Depends() factory
│
├── domain/
│   ├── entities/user.py
│   ├── enums/user_status.py
│   └── contracts/user_repository.py
│
├── application/
│   └── use_cases/
│       ├── get_profile.py
│       ├── update_profile.py
│       ├── list_users.py
│       ├── lock_user.py
│       └── unlock_account.py
│
├── infrastructure/
│   └── persistence/
│       ├── models/user_model.py
│       ├── mappers/user_mapper.py
│       └── repositories/user_repository_impl.py
│
└── presentation/
    ├── controllers/
    │   ├── user_controller.py                 # public — FE gọi, yêu cầu session cookie
    │   └── internal_controller.py             # nội bộ — module khác gọi qua HTTP khi tách service
    ├── dependencies/user_dependencies.py
    └── schemas/user_schema.py