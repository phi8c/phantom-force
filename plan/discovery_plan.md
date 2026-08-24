Ừ, lần này mình sẽ **khóa cách làm** theo đúng thứ tự bạn muốn:

> **Dependency lớn → DB/config/seed → persistence → module structure → worker/runtime → rồi mới application/service/use case.**

Không code lỡ cỡ.

Và mình xác nhận thêm một điểm: **mình đã kiểm tra nguồn hiện có về `knowledge_space`; trong source hiện tại mình không thấy bảng/model `knowledge_space` được xác định rõ.** Vì vậy không nên giả định nó đã tồn tại. Ta sẽ coi đây là **dependency mới cần tạo**, rồi seed các engine/config cần thiết.

Mình cũng sẽ **không lấy các tài liệu Phase cũ làm kiến trúc hiện tại**; phần dưới chỉ dựa trên những gì bạn vừa chốt + source structure hiện tại.

---

# I. Dependency lớn nhất: Knowledge Space Configuration

Trước khi Ingest chạy, phải biết:

```text
Knowledge Space
│
├── Data Hub / Source
│
├── Extraction Engine
│
├── Chunking Strategy
│
├── Classification
│
└── Embedding Model
```

Đây là **configuration của Knowledge Space**, không phải configuration của từng worker.

## 1. `knowledge_spaces`

Nếu chưa có thì tạo.

```text
knowledge_spaces
----------------
id
name
code
description
status

extraction_engine_id
chunking_strategy_id
classification_engine_id   NULL
embedding_model_id

configuration JSONB

created_at
updated_at
```

### Ý nghĩa

Ví dụ:

```text
Knowledge Space: HR
Extraction: Docling
Chunking: Paragraph
Classification: Azure AI
Embedding: text-embedding-3-small
```

---

# II. Các bảng lookup/config + seed

Không hardcode engine trong Python.

## `extraction_engines`

```text
id
code
name
provider
configuration
enabled
```

Seed:

```text
DOCLING
AZURE_DOCUMENT_INTELLIGENCE
```

---

## `chunking_strategies`

```text
id
code
name
configuration
enabled
```

Seed đúng **2 engine/strategy hiện tại của project**, không tự thêm cái mới.

---

## `classification_engines`

```text
id
code
name
provider
configuration
enabled
```

Có thể có nhiều model/engine.

Knowledge Space:

```text
classification_engine_id = NULL
```

→ classification disabled.

---

## `embedding_models`

```text
id
code
name
provider
dimension
configuration
enabled
```

Seed model hiện tại đang dùng:

```text
text-embedding-3-small
dimension = 1536
```

Không hardcode `1536` trong code nữa.

---

# III. Một điểm rất quan trọng: Classification

Không nên tạo:

```text
classification_engine_id = PUBLIC
```

Không.

Nếu Knowledge Space:

```text
classification_engine_id = NULL
```

thì ingest pipeline hiểu:

```text
classification disabled
```

và khi tạo chunk:

```text
classification = PUBLIC
classification_level = 0
```

Đây là **default behavior của ingest**, không cần gọi Classification worker.

---

# IV. Embedding

Knowledge Space có:

```text
embedding_model_id
```

và **chỉ có một embedding model active trong Knowledge Space**.

Ví dụ:

```text
Knowledge Space A
    ↓
text-embedding-3-small
    ↓
1536
```

Một ingest run không được tự chọn:

```text
model A
```

hay:

```text
model B
```

khác với Knowledge Space.

Nếu đổi model:

> đó là operation thay đổi/rebuild embedding của Knowledge Space, không phải option bình thường của một ingest run.

Cái này giúp toàn bộ vector trong một Knowledge Space cùng semantic space.

---

# V. Có cần thêm queue không?

Hiện bạn có:

```text
download_queue
extract_queue
chunk_queue
embedding_queue
classification_queue
```

Mình đề xuất **thêm đúng 1 queue:**

```text
discovery_queue
```

### Vì sao?

Discovery cũng có nhiều worker.

Ví dụ:

```text
Discovery Queue
    │
    ├── Worker 1
    ├── Worker 2
    ├── Worker 3
    └── Worker N
```

Nó nhận workload kiểu:

```text
DiscoveryTask
    source_id
    knowledge_space_id
    ingestion_run_id
    scope
    inventory_version
```

Worker lấy candidate batch từ DB rồi đưa xuống Download Queue.

---

## Không cần thêm

### `orchestration_queue`

**Không cần.**

Orchestration là control plane, không phải processing stage.

### `retry_queue`

**Không cần queue riêng.**

Retry là metadata/policy của task + khả năng retry của queue.

### `progress_queue`

**Không cần.**

Progress nằm trong DB.

### `storage_queue`

**Không cần.**

Download xong lưu storage rồi gửi work tiếp.

---

# VI. Toàn bộ runtime lúc này

Đây mới là flow mình muốn dùng:

```text
                 Ingestion Run
                      │
                      ▼
               Discovery Queue
                 │   │   │
                 ▼   ▼   ▼
              Discovery Workers
                 │
          batch 1 / batch 2 / batch 3
                 │
                 ▼
            Download Queue
          ┌──────┼──────┐
          ▼      ▼      ▼
       Worker  Worker  Worker
          │
          ▼
      Content Storage
          │
          ▼
       Extract Queue
          │
       Workers(N)
          │
          ▼
       Chunk Queue
          │
       Workers(N)
          │
          ├──────────────┐
          ▼              ▼
 Classification       Embedding
 Queue                Queue
    │                    │
 Workers(N)           Workers(N)
```

Điểm quan trọng:

```text
Discovery Worker 1
    batch 1 → Download Queue
    batch 2 → Download Queue
    batch 3 → Download Queue
```

không đợi.

Download cũng vậy:

```text
Download Worker
    batch 1 → Extract Queue
    batch 2 → Extract Queue
    batch 3 → Extract Queue
```

không đợi Extraction batch trước hoàn thành.

**Queue chính là buffer giữa các stage.**

---

# VII. Local chạy thế nào?

Local **không nên chạy 1 process chứa tất cả worker** theo kiểu:

```text
python main.py
```

rồi spawn linh tinh.

Ta nên tổ chức logical worker process theo queue.

Ví dụ local:

```text
API
 ├── Discovery Worker × 2
 ├── Download Worker × 2
 ├── Extract Worker × 2
 ├── Chunk Worker × 2
 ├── Classification Worker × 1
 └── Embedding Worker × 1
```

Queue có thể dùng implementation local tương ứng.

Điểm quan trọng là:

> **Worker code không được biết mình đang chạy local hay production.**

Worker chỉ biết:

```text
consume task
→ execute
→ persist
```

---

# VIII. Production

Deploy nhiều VM:

```text
VM 1
├── API
├── Discovery Worker × N
└── Orchestration

VM 2
├── Download Worker × N
└── Extract Worker × N

VM 3
├── Chunk Worker × N
├── Classification Worker × N
└── Embedding Worker × N
```

Hoặc Kubernetes/container scale riêng từng deployment.

Ví dụ bottleneck Extraction:

```text
extract-worker
1 → 5 → 20 replicas
```

không cần scale:

```text
embedding-worker
```

Queue tự giữ backlog.

Đó mới là lý do chúng ta chia queue theo stage.

---

# IX. Folder structure của `module/ingest/discovery`

Mình không muốn nhét Discovery vào `data_hub`.

Hai cục này khác responsibility.

```text
module/
└── ingest/
    ├── discovery/
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── ingestion_document_state.py
    │   │   │   └── ...
    │   │   │
    │   │   ├── enums/
    │   │   │   └── ingestion_document_status.py
    │   │   │
    │   │   └── repositories/
    │   │       ├── document_repository.py
    │   │       └── ingestion_document_state_repository.py
    │   │
    │   ├── application/
    │   │   ├── requests/
    │   │   │   └── discover_batch_request.py
    │   │   ├── responses/
    │   │   │   └── discover_batch_response.py
    │   │   └── use_cases/
    │   │       └── discover_batch.py
    │   │
    │   ├── infrastructure/
    │   │   └── persistence/
    │   │       ├── models/
    │   │       │   ├── document_model.py
    │   │       │   └── ingestion_document_state_model.py
    │   │       ├── mappers/
    │   │       │   ├── document_mapper.py
    │   │       │   └── ingestion_document_state_mapper.py
    │   │       └── repositories/
    │   │           ├── document_repository_impl.py
    │   │           └── ingestion_document_state_repository_impl.py
    │   │
    │   └── presentation/
    │       └── ...
    │
    ├── orchestration/
    ├── download/
    ├── extraction/
    ├── chunking/
    ├── classification/
    └── embedding/
```

`data-platform/data-hub` **không nằm trong `ingest/discovery`**.

Nó chỉ cung cấp public capability:

```text
Data Hub
    ↓
list files
```

Discovery Ingest tiêu thụ result đó thông qua public contract.

---

# X. Persistence của Discovery

Sau khi dependency Knowledge Space được tạo, Discovery cần:

### Existing

```text
documents
```

sửa lại thành inventory thuần.

### New

```text
ingestion_document_states
```

### Existing

```text
ingestion_runs
```

thêm:

```text
knowledge_space_id
inventory_version
```

---

## `documents`

Nó trả lời:

> Data Hub hiện có file gì?

Không trả lời:

> File này đang ingest tới đâu?

---

## `ingestion_document_states`

Nó trả lời:

> Trong run này, version này của document đang ở trạng thái gì?

Ví dụ:

```text
document_id
ingestion_run_id
source_version
status
created_at
updated_at
```

---

# XI. Discovery enums

Chỉ cần:

```text
IngestionDocumentStatus

PENDING
QUEUED
PROCESSING
COMPLETED
FAILED
```

Và nếu `IngestionRun` đã có:

```text
PENDING
RUNNING
COMPLETED
FAILED
```

thì giữ enum đó ở orchestration.

**Không tạo thêm 5 enum chỉ để Discovery cho đẹp.**

---

# XII. Discovery repositories

### `document_repository.py`

Cần:

```text
get_by_id()
get_by_external_id()
list_by_scope()
count_by_scope()
```

### `ingestion_document_state_repository.py`

Cần:

```text
get_by_document_and_run()
list_pending()
count_pending()
create()
update_status()
```

Nhưng có một hàm cực kỳ quan trọng:

```text
claim_batch()
```

Mình vẫn muốn nó nằm ở **Orchestration**, không nằm trong Discovery.

Discovery:

```text
find candidate
```

Orchestration:

```text
claim candidate
create task
send queue
```

Boundary như vậy sạch hơn.

---

# XIII. Discovery application

Chỉ cần một use case chính:

```text
discover_batch
```

Input:

```text
knowledge_space_id
ingestion_run_id
scope
inventory_version
batch_size
```

Output:

```text
DiscoveryBatch
├── run_id
├── inventory_version
└── items[]
```

Nó không:

* download
* extract
* chunk
* gọi embedding
* gọi classification
* tự xử retry
* tự xử queue

---

# XIV. Dependency map

Trước khi viết Discovery:

```text
                 KNOWLEDGE SPACE
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
    Extraction      Chunking      Classification
      Config         Config          Config
                       │
                       ▼
                  Embedding
                    Config
                       │
                       ▼
                Ingestion Run
                       │
                       ▼
              Discovery Queue
                       │
                       ▼
               Discovery Worker
                       │
                       ▼
                 Platform DB
                       │
                       ▼
                  Candidates
                       │
                       ▼
                 Orchestration
                       │
                       ▼
                Download Queue
```

---

# XV. Thứ tự làm thực tế

Và mình hoàn toàn đồng ý với nguyên tắc **ngoài vào trong** của bạn.

Không làm:

```text
Service
 ↓
Repository
 ↓
"Ủa thiếu table"
```

Mà làm:

### Bước 0 — Dependency

```text
1. Knowledge Space table
2. Extraction Engine table
3. Chunking Strategy table
4. Classification Engine table
5. Embedding Model table
6. Seed data
7. Knowledge Space seed/config
```

**Xong bước này mới bắt đầu Ingest.**

### Bước 1 — DB/Migration

```text
documents
ingestion_runs
ingestion_document_states
```

### Bước 2 — Persistence

```text
Model
→ Mapper
→ Repository
```

### Bước 3 — Domain

```text
Entity
Enum
Repository Contract
```

### Bước 4 — Discovery Application

```text
Request
Response
UseCase
```

### Bước 5 — Worker

```text
Discovery Worker
```

### Bước 6 — Queue adapter

Chỉ dùng contract hiện tại; queue provider cụ thể vẫn tách.

### Bước 7 — Integration

```text
Data Hub Discovery
       ↓
Ingest Discovery
       ↓
Orchestration
       ↓
Download Queue
```

---

## Một điểm mình muốn **khóa trước khi code**

Hiện tại source structure có `infrastructure/configuration` và `registry/provider_registry.py`, còn persistence được tách thành `models / mappers / repositories`. 

Vậy **Knowledge Space configuration nên là dependency của toàn bộ Ingest**, không nên để từng module tự đọc configuration riêng.

Tức:

```text
KnowledgeSpace
       ↓
Ingestion Configuration Snapshot
       ↓
Discovery / Download / Extraction / Chunking / Classification / Embedding
```

Mỗi run nên **chụp configuration tại thời điểm bắt đầu**. Nếu admin thay:

```text
Chunking = Engine B
```

giữa lúc run 10.000 files đang chạy, run đó **không được nửa A nửa B**.

Đây là lý do mình muốn thêm `configuration_snapshot` hoặc version/config reference vào `ingestion_runs` khi chốt Orchestration. **Chưa code field này ngay ở Discovery**, nhưng nó là dependency cần khóa trong thiết kế tổng thể.

Và hiện tại mình **không thấy `knowledge_space` được xác nhận trong source**, nên phần này nên làm trước Discovery. Sau khi bạn duyệt dependency này, chúng ta mới khóa **exact DB schema + seed + file list của Dependency phase**, rồi mới bước vào persistence Discovery.
