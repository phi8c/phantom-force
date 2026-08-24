Đúng. Và trước hết mình sửa một điểm: **từ đây mình sẽ không lấy `BE .Phase .2/.3` hay bất kỳ tài liệu cũ nào làm căn cứ nữa**. Bạn đã nói đó là tài liệu đã bỏ thì coi như **không tồn tại trong thiết kế hiện tại**. Mình chỉ bám vào:

1. Những gì bạn vừa chốt trong cuộc trao đổi này.
2. Source/code hiện tại bạn chỉ định.
3. Các file nguồn bạn đã đưa làm context khi chúng còn phù hợp.

Không tự lôi kiến trúc cũ/event cũ vào nữa.

---

# 1. Trước hết chốt lại Discovery

Cách bạn mô tả bây giờ mình thấy có **2 Discovery khác nhau**, và phải đặt tên rõ để không lẫn.

### A. Data Hub Discovery

Nằm bên **Data Hub/Data Platform provider**.

Nhiệm vụ:

```text
SharePoint / S3 / MinIO / ...
        ↓
Data Hub Discovery
        ↓
list file/folder/item
```

Nó biết provider đang discovery kiểu gì.

Bạn nói giả sử **cục này đã refactor xong**, tức:

```text
DiscoveryProvider
    ↓
List<Item>
```

Ingest không cần biết nó dùng Graph API, S3 API, pagination hay gì.

---

### B. Ingest Discovery

Đây mới là cục chúng ta đang làm.

Nó **không đi discovery trực tiếp trên Data Hub**.

Nó làm:

```text
Platform DB Inventory
        ↓
Ingest Discovery
        ↓
chọn những document cần ingest
        ↓
batch
```

Và đây là cách mình chọn là **tối ưu nhất cho kiến trúc của chúng ta**.

---

# 2. Vì sao chọn DB Discovery?

Giả sử Data Hub có:

```text
Site A
    1,000,000 files
```

Data Hub Discovery có thể trả:

```text
file 1
file 2
...
file 1,000,000
```

Nhưng Ingest cần biết:

```text
file nào đã ingest
file nào chưa
file nào đang ingest
file nào failed
file nào thuộc scope
file nào thuộc version nào
```

Nếu mỗi lần ingest lại gọi Data Hub rồi mới đối chiếu:

```text
Data Hub
    ↓
1,000,000 items
    ↓
check DB
    ↓
lọc
```

thì Discovery của Ingest bị phụ thuộc trực tiếp vào Data Hub.

**Không cần.**

---

# 3. Kiến trúc đúng nên là 2 tầng

```text
                 DATA HUB
                    │
                    │ Data Hub Discovery
                    ▼
             Data Hub Inventory
                    │
                    │ synchronize
                    ▼
              PLATFORM DB
          ┌───────────────────┐
          │ source            │
          │ site              │
          │ folder            │
          │ document          │
          │ external version  │
          └─────────┬─────────┘
                    │
                    │ Ingest Discovery
                    ▼
              Ingestion Run
                    │
                  batch
                    │
                    ▼
                 Download
```

**Data Hub Discovery = đồng bộ dữ liệu về platform.**

**Ingest Discovery = chọn dữ liệu trong platform để tạo workload.**

Hai cái này không phải một.

---

# 4. Có cần "đóng băng" Data Hub khi ingest không?

Theo mình: **không nên khóa API upload.**

Cách bạn đưa ra:

> discovery tại thời điểm đó lưu DB, sau đó y như cách 1, tại thời điểm đó trên site ngăn mọi API upload

thì đảm bảo consistency, nhưng cái giá là **ingest trở thành operation có downtime/lock source**.

Không đáng.

Thay vào đó chúng ta dùng **snapshot/version của inventory**.

Ví dụ Data Hub sync lúc:

```text
inventory_version = 105
```

DB có:

```text
Site A
Folder X
    file 1
    file 2
    ...
```

User bấm ingest.

Ingestion Run lấy:

```text
source_id
scope
inventory_version = 105
```

Và Discovery chỉ làm việc trên inventory đó.

Trong lúc ingest:

```text
Data Hub
    file 1001 uploaded
```

không ảnh hưởng run hiện tại.

Run hiện tại xử lý:

```text
version 105
```

Lần sync sau:

```text
version 106
```

thì file 1001 mới trở thành candidate cho một run khác.

---

# 5. Đây cũng giải quyết vấn đề batch của bạn

Ví dụ inventory:

```text
1000 documents
inventory_version = 105
```

Ingestion Run:

```text
run_id = R1
scope = Site A
inventory_version = 105
```

Discovery lấy:

```text
batch 1 = 100 files
```

Download bắt đầu xử lý batch 1.

Discovery **không cần quay lại Data Hub**.

Nó tiếp tục:

```text
batch 2 = next 100
batch 3 = next 100
...
```

và lọc dựa trên **DB state của run/document**, không dựa vào Data Hub.

---

# 6. Nhưng có một vấn đề quan trọng: không được thêm `ingested = true` vào `documents`

Đây là chỗ mình muốn sửa lại thiết kế trước đó.

Ví dụ:

```text
document A
```

hôm nay ingest:

```text
version 10
```

sau đó Data Hub file A đổi:

```text
version 11
```

Ngày mai ingest lại.

Nếu `documents.ingested = true` thì không đủ thông tin.

Cho nên:

```text
documents
```

chỉ là **inventory**.

Còn trạng thái ingest phải có persistence riêng.

---

# 7. Discovery cần một bảng mới

Mình đề xuất:

```text
document_ingestion_states
```

hoặc tên rõ hơn:

```text
ingestion_document_states
```

Mình nghiêng về:

```text
ingestion_document_states
```

vì ownership thuộc **Ingest**.

---

## Table

```text
ingestion_document_states
```

### Fields

```text
id
ingestion_run_id
document_id

inventory_version
source_version
content_hash

status

discovered_at
started_at
completed_at
failed_at

created_at
updated_at
```

Nhưng **không phải tất cả field này Discovery tự quản lý**.

Đây là persistence dùng chung giữa Discovery + Orchestration.

---

# 8. Vì vậy Discovery cần persistence tối thiểu nào?

Nếu chỉ xét **cục Discovery**, mình muốn nó có:

### Giữ

```text
documents
```

để làm inventory.

### Thêm

```text
ingestion_document_states
```

để biết:

```text
document X
đã được đưa vào ingestion run nào
với version nào
trạng thái gì
```

### Không dùng

```text
documents.processing_status
```

vì status đó thuộc pipeline.

---

# 9. `documents` cần sửa gì?

File cũ:

```text
app/infrastructure/persistence/models/document_model.py
```

sẽ chuyển thành:

```text
app/infrastructure/persistence/models/discovery/document_model.py
```

**DB `documents` giữ**, không tạo bảng mới cho inventory.

Các field inventory cần giữ:

```text
id
source_id
external_file_id

file_name
file_extension
file_size_bytes

source_file_url
provider_metadata

content_hash
last_modified_at

created_at
updated_at
```

Và cần thêm:

```text
external_version
```

### `external_version` để làm gì?

Không phải provider nào cũng có `version`.

Cho nên:

```text
external_version nullable
```

Nếu SharePoint có version:

```text
external_version = "42"
```

Nếu provider không có:

```text
external_version = NULL
```

`content_hash` vẫn có thể dùng để phát hiện thay đổi nếu Data Hub trả được hash.

---

# 10. Bỏ khỏi `documents`

Những cái này:

```text
processing_status
processing_error
temp_file_path
last_ingested_at
```

không còn thuộc Discovery.

Lý do:

```text
documents
=
"What exists in Data Hub?"
```

không phải:

```text
"What is Ingest doing with it?"
```

---

# 11. `ingestion_document_states` mới là nơi trả lời câu hỏi "đã ingest chưa"

Ví dụ:

```text
document_id = A
source_version = 42
status = COMPLETED
```

thì Discovery biết:

> A version 42 đã ingest.

Nếu Data Hub sync:

```text
A version = 43
```

thì:

```text
document_id = A
source_version = 43
```

không còn match state completed của version 42.

→ A trở thành candidate.

Đây là cách tốt hơn rất nhiều so với:

```text
ingested = true
```

---

# 12. Enum của Discovery

Discovery thật ra **không cần nhiều enum**.

## `DocumentSyncStatus`

Cho inventory synchronization:

```text
PENDING
SYNCING
SYNCED
FAILED
```

Nhưng cái này thuộc quá trình **Data Hub → DB synchronization**.

Nếu Data Hub module đã sở hữu sync thì mình **không muốn Discovery Ingest sở hữu enum này**.

---

## Ingest document state

Cái này mới thuộc Ingest:

```text
IngestionDocumentStatus
```

Mình đề xuất:

```text
PENDING
QUEUED
PROCESSING
COMPLETED
FAILED
```

Nhưng có một điểm:

**Discovery không được tự quản lý hết enum này.**

Discovery chỉ thực sự quan tâm:

```text
PENDING
COMPLETED
```

để chọn candidate.

Orchestration/worker mới update:

```text
QUEUED
PROCESSING
FAILED
```

Đây chính là chỗ module ownership phải rõ.

---

# 13. Repo Discovery cần gì?

File cũ:

```text
app/domain/repositories/document_repository.py
```

sẽ chuyển thành:

```text
app/domain/repositories/discovery/document_repository.py
```

hoặc nếu module structure đang dùng `module/...` như bạn nói thì đặt dưới module Discovery tương ứng.

Repository cần các operation:

### 1. Lấy document theo ID

```python
get_by_id(document_id)
```

### 2. Lấy document theo external ID

```python
get_by_external_id(source_id, external_file_id)
```

### 3. Upsert inventory

```python
upsert_inventory(...)
```

Đây phục vụ Data Hub synchronization.

### 4. Lấy documents theo scope

```python
list_by_scope(
    source_id,
    scope_type,
    scope_id,
    ...
)
```

Nhưng đây mới chỉ là inventory.

---

# 14. Repo thứ hai: ingestion document state

File mới:

```text
domain/repositories/discovery/ingestion_document_state_repository.py
```

Các method cần có:

```text
get(document_id, ingestion_context)
```

```text
get_completed_version(document_id)
```

```text
list_pending_documents(scope, version, limit)
```

và quan trọng nhất:

```text
claim_next_batch(...)
```

Nhưng ở đây mình muốn cẩn thận:

**claim batch là responsibility của Orchestration hay Discovery?**

Theo architecture bạn vừa mô tả, mình nghiêng về:

```text
Discovery
    ↓
find candidate batch
    ↓
Orchestration
    ↓
claim/dispatch task
```

Discovery **không nên trở thành task manager**.

Nó chỉ trả:

```text
DiscoveryResult
```

ví dụ:

```json
{
  "run_id": "...",
  "inventory_version": 105,
  "items": [...]
}
```

Orchestration mới quyết định:

```text
batch này đã claim chưa?
worker nào?
retry?
queue?
```

---

# 15. Vì vậy Discovery không cần `claim_next_batch`

Mình sửa lại điểm này để boundary sạch hơn.

Discovery repository chỉ cần:

```text
list_candidates(...)
count_candidates(...)
```

Ví dụ:

```python
list_candidates(
    source_id,
    scope,
    inventory_version,
    limit=100,
)
```

Còn Orchestration:

```text
candidate documents
       ↓
create/claim processing tasks
       ↓
queue
```

---

# 16. Nhưng làm sao batch 2 không lấy lại batch 1?

Không để Discovery tự nhớ cursor.

Nó dựa vào persistence state.

Ví dụ:

```text
1000 documents
```

Sau batch 1:

```text
100 documents
→ ingestion_document_states
→ QUEUED/PROCESSING
```

Query batch 2:

```sql
documents
WHERE scope = X
AND NOT EXISTS (
    ingestion_document_state
    WHERE document_id = documents.id
    AND run_id = current_run
)
LIMIT 100
```

Như vậy:

```text
batch 1
→ đã có state

batch 2
→ không match state
→ được lấy
```

Không cần:

```text
offset = 100
```

Đây là **rất quan trọng**.

Không dùng offset để làm processing cursor.

---

# 17. Và inventory snapshot phải nằm ở Run

Đây là một field mình nghĩ cần thêm vào `ingestion_runs`:

```text
inventory_version
```

hoặc:

```text
discovery_version
```

Mình chọn:

```text
inventory_version
```

Vì nó mô tả chính xác:

> Run này đang ingest inventory snapshot nào.

Ví dụ:

```text
ingestion_runs
────────────────────
id = R1
source_id = S1
scope_type = SITE
scope_data = {...}
inventory_version = 105
```

---

# 18. Vậy Discovery flow hoàn chỉnh

Giả sử Data Hub đã sync xong:

```text
Data Hub
   ↓
Data Hub Discovery
   ↓
Platform DB
   ↓
inventory_version = 105
```

User:

```text
Site A
```

bấm Ingest.

### Bước 1

Orchestration tạo:

```text
IngestionRun
inventory_version = 105
scope = Site A
```

### Bước 2

Discovery:

```text
list_candidates(
    Site A,
    inventory_version=105,
    limit=100
)
```

→ 100 files.

### Bước 3

Orchestration dispatch:

```text
100 files
↓
Download Queue
```

### Bước 4

Discovery tiếp tục:

```text
list_candidates(...)
```

→ 100 file tiếp theo.

**Không chờ Download.**

---

# 19. Nếu Download nhanh hơn Extraction?

Đó không phải vấn đề Discovery.

```text
Discovery
   ↓
Download Queue
   ↓
Download Workers
   ↓
Extraction Queue
   ↓
Extraction Workers
```

Queue làm buffer.

Discovery vẫn có thể tiếp tục tạo batch cho tới khi orchestration/queue áp dụng backpressure.

Đây là lý do Discovery **không được biết Download đang xử lý gì**.

---

# 20. Dependencies của Discovery

Nếu giả sử:

> Data Hub Discovery đã hoàn thành, trả list item được.

thì Ingest Discovery chỉ cần:

```text
Discovery
│
├── Document Repository
│
├── Ingestion Document State Repository
│
├── Ingestion Run context
│
└── [Data Hub result contract nếu cần reconcile]
```

**Không cần:**

```text
Download Service
Extraction
Chunking
Embedding
Classification
Queue Provider
Event Bus
```

Đặc biệt **không Event Bus**.

---

# 21. File list cho Discovery Persistence

Theo đúng yêu cầu "file cũ → file mới":

### Existing — sửa

```text
app/infrastructure/persistence/models/document_model.py
    ↓
app/infrastructure/persistence/models/discovery/document_model.py
```

### Existing — sửa

```text
app/infrastructure/persistence/mappers/document_mapper.py
    ↓
app/infrastructure/persistence/mappers/discovery/document_mapper.py
```

### Existing — sửa

```text
app/infrastructure/persistence/repositories/document_repository_impl.py
    ↓
app/infrastructure/persistence/repositories/discovery/document_repository_impl.py
```

### Existing — sửa

```text
app/domain/entities/document.py
    ↓
module/discovery/domain/entities/document.py
```

### Existing — sửa

```text
app/domain/repositories/document_repository.py
    ↓
module/discovery/domain/repositories/document_repository.py
```

---

### New

```text
module/discovery/domain/entities/ingestion_document_state.py
```

```text
module/discovery/domain/repositories/ingestion_document_state_repository.py
```

```text
app/infrastructure/persistence/models/discovery/ingestion_document_state_model.py
```

```text
app/infrastructure/persistence/mappers/discovery/ingestion_document_state_mapper.py
```

```text
app/infrastructure/persistence/repositories/discovery/ingestion_document_state_repository_impl.py
```

### DB migration

```text
documents
    + external_version

ingestion_runs
    + inventory_version

ingestion_document_states
    NEW
```

---

# 22. Nhưng có một thứ mình **chưa muốn thêm vào Discovery**

`sync_state`.

Nếu Data Hub/Data Platform đã có một cục chịu trách nhiệm:

```text
Data Hub
    ↓
synchronize
    ↓
Platform inventory
```

thì `sync_state` thuộc **inventory synchronization**, không thuộc Ingest Discovery.

Ingest Discovery chỉ tiêu thụ:

```text
documents
+
inventory_version
```

Nó không cần biết:

```text
delta token
Graph pagination
S3 continuation token
...
```

Đó chính xác là abstraction boundary bạn muốn.

---

# 23. Chốt phương án

Mình chọn phương án:

> **Data Hub Discovery → đồng bộ inventory về Platform DB → tạo inventory version → Ingest Run chụp version đó → Ingest Discovery query DB theo scope + version + ingestion state → trả batch → Orchestration dispatch.**

Không chọn:

> Ingest Discovery trực tiếp query Data Hub mỗi lần lấy batch.

Và cũng **không chọn lock Data Hub/API upload trong suốt ingestion**.

Lý do cốt lõi:

```text
Data Hub Discovery
= Source synchronization

Ingest Discovery
= Work selection
```

Hai nhiệm vụ khác nhau.

---

### Discovery persistence sau khi chốt

```text
                 PLATFORM DB
                     │
        ┌────────────┴────────────┐
        │                         │
     documents            ingestion_document_states
        │                         │
   inventory                    ingest state
        │                         │
        └──────────┬──────────────┘
                   │
            Ingest Discovery
                   │
          scope + version
                   │
                batch
                   │
                   ▼
             Orchestration
```

**Đây là cục Discovery mình nghĩ đã đủ rõ để khóa DB design.** Chưa cần đụng service/use case/worker. Bước tiếp theo đúng quy trình bạn đặt ra là mình có thể chốt riêng **exact schema của 3 phần `documents`, `ingestion_runs`, `ingestion_document_states`: từng column, type, nullable, unique/index, FK nào giữ/bỏ và lý do**, rồi từ schema đó mới lập exact persistence file list để bắt đầu sửa DB.


#################################################################################################


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
