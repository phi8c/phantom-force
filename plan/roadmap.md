Đúng. Giờ mình hiểu chính xác cái bạn đang muốn nói — và **mô hình này không phải "parallel branches" đơn thuần**, mà là **streaming pipeline có stage-to-stage buffering/backpressure**.

Ví dụ đúng phải là:

```text
Discovery
 Worker 1 ── batch 1 ──→ Download Queue
 Worker 2 ── batch 2 ──→ Download Queue
 Worker 3 ── batch 3 ──→ Download Queue
              ...
                    ↓
              Download Workers
                    ↓
              Extraction Queue
                    ↓
              Extraction Workers
                    ↓
               Chunk Queue
                    ↓
                Chunk Workers
                    ↓
              ChunkBatchReady
               ┌────┼────┬─────┐
               ↓    ↓    ↓     ↓
              C1    E1   Entity ...
             Queue Queue Queue
```

Và quan trọng là:

```text
Discovery Worker
    batch 1 → Download
    batch 2 → Download
    batch 3 → Download
    batch 4 → Download
```

**Discovery không đợi batch 1 download xong.**

Nếu Download nhanh hơn Extraction:

```text
Download
 batch 1 ─┐
 batch 2 ─┤
 batch 3 ─┤──→ Extraction Queue
 batch 4 ─┘
```

Extraction chưa xử lý kịp thì queue giữ batch.

Nếu Extraction xử lý xong batch 1:

```text
Extraction
 batch 1 → Chunk Queue

 batch 2 đang chờ
 batch 3 đang chờ
```

Nó lấy batch 2.

Đây chính là lý do **queue là buffer giữa các stage**, còn worker chỉ xử lý batch. Source Architecture của bạn cũng ghi rõ mục tiêu là Streaming Pipeline, Worker stateless, Queue dùng để phân phối và Azure Service Bus load-balance các worker.  

Và sau Chunking thì `ChunkBatch` trở thành processing unit độc lập; các AI pipeline subscribe event riêng. 

---

# Bây giờ quay lại đúng việc bạn yêu cầu: Persistence Refactor

Lần này mình không nói kiểu "giữ/sửa nhiều" chung chung nữa.

Mình sẽ lấy:

* source structure mới bạn đã upload;
* import map hiện tại;
* persistence code thật trong repo;
* architecture Phase 2/3;

rồi lập **migration/refactor map**.

Source structure hiện tại vẫn giữ `infrastructure/persistence/{models,mappers,repositories}` và workers theo stage.

Import map cũng xác nhận persistence cũ đang được nhiều worker dùng chéo, đặc biệt `chunk_batch_repository_impl`, `document_chunk_repository_impl`, `document_processing_task_impl`. 

---

# 1. `ingestion_source_model.py`

### Cũ

```text
app/infrastructure/persistence/models/ingestion_source_model.py
```

### Mới

```text
app/infrastructure/persistence/models/ingestion_source_model.py
```

### DB

```text
ingestion_sources
```

### Quyết định

**GIỮ FILE — SỬA MODEL**

Hiện tại:

```text
id
name
source_type
enabled
provider_type
provider_configuration
created_at
updated_at
```

Source model hiện tại thực tế đúng là đang chứa `source_type`, `provider_type`, configuration và enabled.

### Thay đổi DB

#### Giữ

```text
id
name
source_type
provider_type
provider_configuration
enabled
created_at
updated_at
```

#### Thêm

```text
external_source_id
```

### Tại sao?

Discovery cần phân biệt:

```text
internal source id
        ↓
UUID của hệ thống mình

external_source_id
        ↓
ID của SharePoint / Drive / provider
```

Không hardcode external ID.

---

### Không bỏ `provider_configuration`

Không bỏ.

Vì source có configuration riêng:

```json
{
    "tenant_id": "...",
    "site_id": "...",
    "drive_id": "..."
}
```

nhưng đây là **configuration của source**, không phải enum.

---

# 2. `sync_state_model.py`

### Cũ

```text
app/infrastructure/persistence/models/sync_state_model.py
```

### Mới

```text
app/infrastructure/persistence/models/sync_state_model.py
```

### DB

```text
sync_states
```

### Quyết định

**GIỮ — SỬA**

Cũ:

```text
id
source_id
delta_token
last_sync_at
```

### DB mới

```text
id
source_id

delta_token

status

last_sync_started_at
last_sync_completed_at

last_error

created_at
updated_at
```

### Thêm `status`

Discovery không chỉ cần biết delta token.

Nó cần biết:

```text
IDLE
RUNNING
FAILED
```

để scheduler/retry không chạy đè một sync đang chạy.

### `last_sync_at` đổi thành

```text
last_sync_completed_at
```

Vì `last_sync_at` không phân biệt:

```text
sync bắt đầu
```

với

```text
sync hoàn thành
```

Trong streaming architecture điều này quan trọng.

---

# 3. `document_model.py`

### Cũ

```text
app/infrastructure/persistence/models/document_model.py
```

### Mới

```text
app/infrastructure/persistence/models/document_model.py
```

### DB

```text
documents
```

### Quyết định

**GIỮ — SỬA**

Document phải là **inventory/source metadata**, không phải pipeline state.

---

## Giữ

```text
id
source_id
external_file_id
provider_metadata

file_name
file_extension
file_size_bytes

source_file_url

content_hash

last_modified_at

created_at
updated_at
```

---

## Bỏ

```text
processing_status
processing_error
```

### Vì sao?

Document không được sở hữu trạng thái:

```text
DOWNLOADING
EXTRACTING
CHUNKING
EMBEDDING
...
```

Nếu giữ thì Discovery/Document sẽ biết pipeline phía sau.

Trong kiến trúc mới, mỗi batch được đẩy qua queue; worker có thể đang xử lý batch khác nhau cùng lúc.

Một `document.processing_status` không thể biểu diễn chính xác trạng thái streaming đó.

---

## Bỏ

```text
temp_file_path
```

### Vì sao?

Temporary file là runtime artifact của Download/Extraction.

Nó không phải thuộc tính lâu dài của Document.

Nếu worker chết:

```text
temp file
```

không thể là source of truth.

---

## `original_file_path`

**Không bỏ nếu nó thực sự là persistent storage path.**

Nhưng đổi nghĩa rõ ràng thành:

```text
original_file_storage_path
```

hoặc tương đương.

Nó phải trỏ tới object storage persistent.

Không phải local temp path.

---

## `last_ingested_at`

### Không nên nằm ở Document nữa.

Chuyển concept sang:

```text
sync / ingestion run
```

Vì một document có thể được ingest lại nhiều lần.

---

# 4. `ingestion_run_model.py`

### Cũ

```text
app/infrastructure/persistence/models/ingestion_run_model.py
```

### DB cũ

```text
ingestion_jobs
```

### Mới

```text
app/infrastructure/persistence/models/ingestion_run_model.py
```

### DB

Đổi tên:

```text
ingestion_runs
```

### Quyết định

**GIỮ FILE — SỬA TABLE**

---

## Giữ

```text
id
source_id
trigger_type
status
scope_type
scope_data
configuration
started_at
finished_at
created_at
```

---

## Bỏ

```text
is_build_graph
```

### Vì sao?

Graph là downstream capability.

Ingestion Run không được biết:

```text
có build graph hay không
```

Graph service tự quyết định subscribe event nào / command nào.

---

## Bỏ

```text
total_files
completed_files
failed_files
```

**Không phải bỏ khả năng tracking.**

Mà chuyển tracking xuống execution/task level.

Vì:

```text
1000 documents
```

không còn chạy:

```text
file 1 → file 2 → file 3
```

mà chạy streaming.

Counters kiểu này có thể vẫn tồn tại ở run-level nhưng phải được cập nhật bởi coordinator/event processing, **không phải worker stage tự tiện update**.

Mình sẽ không nhét chúng trở lại model này ở bước DB-first đầu tiên.

---

# 5. `document_processing_task.py`

### Cũ

```text
app/infrastructure/persistence/models/document_processing_task.py
```

### Mới

```text
app/infrastructure/persistence/models/processing_task_model.py
```

### DB

```text
processing_tasks
```

### Quyết định

**RENAME + REWRITE**

Đây là một trong những bảng quan trọng nhất cho streaming pipeline.

---

## Cũ có

```text
document_id
batch_id
task_type
status
retry_count
error_message
started_at
finished_at
created_at
updated_at
```

### Vấn đề

Cũ:

```text
document_id
+
batch_id
```

nhưng không phải stage nào cũng xử lý cùng một loại object.

---

# DB mới

```text
id

run_id

batch_id

task_type

status

attempt

worker_id

error_code
error_message

queued_at
started_at
finished_at

created_at
updated_at
```

---

### `run_id`

Task thuộc ingestion run nào.

### `batch_id`

Task xử lý batch nào.

Có thể nullable cho task ở document-level.

### `task_type`

Ví dụ:

```text
DOWNLOAD
EXTRACTION
CHUNKING
CLASSIFICATION
EMBEDDING
ENTITY
...
```

### `attempt`

Thay `retry_count`.

Vì persistence cần biết:

```text
attempt 1
attempt 2
attempt 3
```

rõ ràng hơn.

### `worker_id`

Để debug:

```text
batch 27
attempt 2
worker vm-03
```

### `queued_at`

Quan trọng cho streaming.

Có thể đo:

```text
queue wait time
```

### `started_at`

Worker thực sự bắt đầu.

### `finished_at`

Worker kết thúc.

Nhờ vậy biết bottleneck nằm ở:

```text
queue
```

hay:

```text
processing
```

---

# 6. `document_pipeline_state_model.py`

### Cũ

```text
app/infrastructure/persistence/models/document_pipeline_state_model.py
```

### DB

```text
document_pipeline_states
```

Cũ:

```text
chunks_ready
classification_ready
embedding_ready
index_event_published
```

## Quyết định

# ❌ BỎ TABLE CŨ

Không sửa.

Không migrate nguyên.

---

### Vì sao?

Nó mô tả pipeline:

```text
chunks
    ↓
classification
    ↓
embedding
    ↓
index
```

trong khi architecture mới:

```text
ChunkBatchReady
       ↓
 ┌─────┼─────┐
 ↓     ↓     ↓
Class Embed Entity
```

và mỗi pipeline có nhiều batch chạy độc lập.

`boolean`:

```text
embedding_ready
```

không thể biểu diễn:

```text
batch 1 embedding done
batch 2 processing
batch 3 queued
batch 4 failed
```

=> **không phù hợp về mặt dữ liệu.**

---

# 7. `chunk_batch_model.py`

### Cũ

```text
app/infrastructure/persistence/models/chunk_batch_model.py
```

### Mới

```text
app/infrastructure/persistence/models/chunk_batch_model.py
```

### DB

```text
document_chunk_batches
```

### Quyết định

**GIỮ — SỬA**

Cũ:

```text
id
document_id
batch_index
total_chunks
classification_completed
embedding_completed
batch_completed
created_at
```

---

## Giữ

```text
id
document_id
batch_index
total_chunks
created_at
```

## Bỏ

```text
classification_completed
embedding_completed
```

### Vì sao?

Chunking không sở hữu hai trạng thái này.

Classification có DB riêng.

Embedding có DB riêng.

---

## `batch_completed`

### Bỏ.

ChunkBatch hoàn thành khi:

```text
chunks persisted
```

và:

```text
ChunkBatchReadyEvent published
```

Không phải khi Classification/Embedding xong.

Architecture cũ cũng đã xác định Chunk Worker chỉ:

```text
Persist ChunkBatch
↓
Publish ChunkBatchReadyEvent
```



---

# 8. `document_chunk_model.py`

### Cũ

```text
app/infrastructure/persistence/models/document_chunk_model.py
```

### Mới

```text
app/infrastructure/persistence/models/document_chunk_model.py
```

### Quyết định

**GIỮ — SỬA NHẸ**

Cũ:

```text
id
batch_id
document_id
chunk_index
title
content
metadata
created_at
```

### DB mới

```text
id
batch_id
document_id
chunk_index
title
content
metadata
created_at
```

**Fields gần như giữ nguyên.**

### Nhưng thay đổi quan trọng:

Bỏ:

```python
ForeignKey("documents.id")
ForeignKey("document_chunk_batches.id")
```

nếu Chunking được tách service/database boundary.

Ta vẫn giữ:

```text
document_id UUID
batch_id UUID
```

nhưng đó là **logical reference**, không phải DB coupling.

---

# 9. `document_extraction_model.py`

### Cũ

```text
app/infrastructure/persistence/models/document_extraction_model.py
```

### Mới

```text
app/infrastructure/persistence/models/document_extraction_model.py
```

### DB

```text
document_extractions
```

### Quyết định

**GIỮ — THÊM TRẠNG THÁI**

Cũ:

```text
id
document_id
structured_content
page_count
created_at
```

### Thêm

```text
status
error_code
error_message
updated_at
```

### Vì sao?

Extraction là một stage độc lập.

Có thể:

```text
batch/document A → extraction processing
document B → extraction failed
document C → extraction completed
```

Persistence phải lưu được lifecycle đó.

---

# 10. `table_asset.py`

### Cũ

```text
app/infrastructure/persistence/models/table_asset.py
```

### Mới

```text
app/infrastructure/persistence/models/table_asset_model.py
```

### DB

```text
table_assets
```

### Quyết định

**RENAME**

Cũ đang khai báo class:

```python
class TableAsset(Base):
```

không đồng nhất naming convention với các model khác.

### Fields

Giữ:

```text
id
document_id
sheet_name
description
row_count
schema_json
storage_path
created_at
```

Chỉ bỏ DB FK tới `documents` nếu Extraction và Document không còn cùng DB ownership.

---

# 11. Classification

### Cũ

```text
app/infrastructure/persistence/models/document_chunk_classification_model.py
```

### Mới

```text
app/infrastructure/persistence/models/document_chunk_classification_model.py
```

### DB

```text
document_chunk_classifications
```

### Quyết định

**GIỮ — SỬA**

Cũ:

```text
chunk_id
model_name
label
confidence
raw_response
created_at
```

### `model_name`

Đổi:

```text
model_id
```

### Vì sao?

Model configuration không hardcode trong code.

Embedding hiện tại đang hardcode:

```text
text-embedding-3-small
1536
8191
```

trong provider config.

Classification cũng phải theo cùng nguyên tắc.

---

### Thêm

```text
status
error_code
error_message
started_at
completed_at
updated_at
```

Vì Classification là processing result độc lập.

---

# 12. Embedding

### Cũ

```text
app/infrastructure/persistence/models/document_chunk_embedding_model.py
```

### Mới

```text
app/infrastructure/persistence/models/document_chunk_embedding_model.py
```

### DB

```text
document_chunk_embeddings
```

### Quyết định

**GIỮ — SỬA**

Cũ:

```text
chunk_id
model_name
embedding
dimension
token_count
created_at
```

### Đổi

```text
model_name
```

→

```text
model_id
```

### Thêm

```text
status
error_code
error_message
started_at
completed_at
updated_at
```

### `dimension`

**GIỮ.**

Dù model configuration có dimension, result vẫn nên lưu dimension thực tế.

Nó giúp phát hiện:

```text
model config = 1536
actual vector = 3072
```

thay vì âm thầm lỗi.

### `Vector(1536)`

Không hardcode nữa.

Đây là chỗ DB migration phải được thiết kế theo dimension configuration.

---

# 13. Một thay đổi rất quan trọng: Batch không cần persistence "để chờ"

Cái bạn vừa mô tả:

> Download xong batch 2 mà Extract chưa xong batch 1 thì Download phải để đâu đó.

**Không phải thêm `waiting` field vào `document` hay `chunk_batch`.**

Nó nằm ở:

```text
Azure Service Bus Queue
```

Queue chính là persistence/buffer của **work chưa được xử lý**.

Còn Supabase là source of truth của **data đã được persist**.

Architecture Phase 2 cũng xác định rõ Queue dùng để phân phối work, còn Supabase lưu intermediate data.  

Cho nên:

```text
Download batch 2 xong
        ↓
persist document/file state
        ↓
publish/extract command
        ↓
Azure Service Bus
        ↓
Download worker rảnh
        ↓
lấy batch 3
```

Không cần:

```text
document.status = WAITING_FOR_EXTRACTION
```

để làm queue.

---

# 14. Nhưng `processing_tasks` vẫn cần

Đây là hai thứ khác nhau:

### Queue

```text
"Việc này đang chờ worker lấy."
```

### `processing_tasks`

```text
"Hệ thống đã giao/ghi nhận việc này và lifecycle của nó là gì?"
```

Ví dụ:

```text
task #123

type = EXTRACTION
batch_id = B17

status = RUNNING
attempt = 2
worker_id = extract-worker-04
started_at = ...
```

Worker chết:

```text
Azure Service Bus
    ↓
retry
```

Task có thể chuyển:

```text
FAILED
```

hoặc tạo attempt tiếp theo.

Đây mới là persistence cần thiết cho orchestration/retry/observability.

---

# 15. Mapper / Repository map

Không chỉ model phải move.

## Discovery

```text
OLD
app/infrastructure/persistence/mappers/
    ingestion_source_mapper.py
    sync_state_mapper.py
    document_mapper.py

OLD repositories/
    source_repository_impl.py
    sync_state_repository_impl.py
    document_repository_impl.py

NEW

app/infrastructure/persistence/mappers/
    discovery/
        ingestion_source_mapper.py
        sync_state_mapper.py
        document_mapper.py

app/infrastructure/persistence/repositories/
    discovery/
        ingestion_source_repository_impl.py
        sync_state_repository_impl.py
        document_repository_impl.py
```

**Lý do:** source structure hiện tại chưa chia persistence theo module, nhưng kiến trúc mới yêu cầu ownership rõ ràng. Cấu trúc hiện tại mới chỉ có generic `models/mappers/repositories`.

---

# 16. Orchestration

```text
app/infrastructure/persistence/mappers/orchestration/
    ingestion_run_mapper.py
    processing_task_mapper.py

app/infrastructure/persistence/repositories/orchestration/
    ingestion_run_repository_impl.py
    processing_task_repository_impl.py
```

Model:

```text
app/infrastructure/persistence/models/orchestration/
    ingestion_run_model.py
    processing_task_model.py
```

---

# 17. Extraction

```text
app/infrastructure/persistence/models/extraction/
    document_extraction_model.py
    table_asset_model.py

app/infrastructure/persistence/mappers/extraction/
    document_extraction_mapper.py
    table_asset_mapper.py

app/infrastructure/persistence/repositories/extraction/
    document_extraction_repository_impl.py
    table_asset_repository_impl.py
```

---

# 18. Chunking

```text
app/infrastructure/persistence/models/chunking/
    chunk_batch_model.py
    document_chunk_model.py

app/infrastructure/persistence/mappers/chunking/
    chunk_batch_mapper.py
    document_chunk_mapper.py

app/infrastructure/persistence/repositories/chunking/
    chunk_batch_repository_impl.py
    document_chunk_repository_impl.py
```

---

# 19. Classification

```text
app/infrastructure/persistence/models/classification/
    document_chunk_classification_model.py

app/infrastructure/persistence/mappers/classification/
    document_chunk_classification_mapper.py

app/infrastructure/persistence/repositories/classification/
    document_chunk_classification_repository_impl.py
```

---

# 20. Embedding

```text
app/infrastructure/persistence/models/embedding/
    document_chunk_embedding_model.py

app/infrastructure/persistence/mappers/embedding/
    document_chunk_embedding_mapper.py

app/infrastructure/persistence/repositories/embedding/
    document_chunk_embedding_repository_impl.py
```

---

# 21. Enum map

Với flow streaming này, persistence cần các enum sau:

```text
app/domain/enums/

source_type.py
provider_type.py              NEW

sync_status.py                NEW

ingestion_status.py
trigger_type.py
scope_type.py

task_type.py
task_status.py

extraction_status.py          NEW

chunk_strategy_type.py

classification_status.py     NEW
embedding_status.py           NEW
```

### Không tạo enum cho:

```text
model_name
provider_configuration
classification label
entity type
```

vì những thứ đó có khả năng configuration/data-driven.

---

# 22. Cái quan trọng nhất: DB ownership sau refactor

Mình chốt map như này:

```text
DISCOVERY
────────────────────────────
ingestion_sources
sync_states
documents


ORCHESTRATION
────────────────────────────
ingestion_runs
processing_tasks


DOWNLOAD
────────────────────────────
[document/file storage metadata nếu cần]
→ chưa tự ý tạo bảng mới ở bước này


EXTRACTION
────────────────────────────
document_extractions
table_assets


CHUNKING
────────────────────────────
document_chunk_batches
document_chunks


CLASSIFICATION
────────────────────────────
document_chunk_classifications


EMBEDDING
────────────────────────────
document_chunk_embeddings


PIPELINE STATE
────────────────────────────
❌ document_pipeline_states
```

Và **không có**:

```text
chunk_batch.classification_completed
chunk_batch.embedding_completed
```

vì chính hai field đó làm persistence cũ biết về downstream pipeline.

---

# 23. Một điểm mình sửa lại so với câu trả lời trước

Lúc trước mình nói:

> bỏ cross-module FK vì microservice.

Điều đó **đúng về nguyên tắc**, nhưng không có nghĩa là cứ thấy `ForeignKey` là bỏ ngay.

Ví dụ:

```text
document_chunks.batch_id
```

và:

```text
document_chunk_batches.id
```

nếu hiện tại Chunking vẫn dùng cùng database thì FK vẫn có giá trị integrity.

Nhưng architecture của bạn nói rõ:

> module chỉ giao tiếp qua public contract và có thể expose HTTP cho microservice.

Do đó **boundary lâu dài không được phụ thuộc vào FK giữa ownership khác nhau**.

Vì vậy khi DB-first refactor này, mình sẽ ưu tiên:

```text
UUID logical reference
```

cho cross-module reference, và chỉ dùng FK **bên trong cùng bounded persistence ownership**.

---

# 24. Tóm lại thành checklist để bắt tay sửa DB

### DELETE

```text
document_pipeline_states
```

và:

```text
classification_completed
embedding_completed
batch_completed
```

khỏi `document_chunk_batches`.

---

### RENAME

```text
ingestion_jobs
→ ingestion_runs

document_processing_tasks
→ processing_tasks

table_asset.py
→ table_asset_model.py
```

---

### ADD

```text
ingestion_sources.external_source_id

sync_states.status
sync_states.last_sync_started_at
sync_states.last_sync_completed_at
sync_states.last_error

document_extractions.status
document_extractions.error_code
document_extractions.error_message
document_extractions.updated_at

processing_tasks.run_id
processing_tasks.attempt
processing_tasks.worker_id
processing_tasks.error_code
processing_tasks.queued_at

classification_results.status
classification_results.model_id
classification_results.error_*

embedding_results.status
embedding_results.model_id
embedding_results.error_*
embedding_results.started_at
embedding_results.completed_at
embedding_results.updated_at
```

---

### REMOVE

```text
documents.processing_status
documents.processing_error
documents.temp_file_path
documents.last_ingested_at

ingestion_runs.is_build_graph

chunk_batches.classification_completed
chunk_batches.embedding_completed
chunk_batches.batch_completed

document_pipeline_states.*
```

---

### KEEP

```text
documents.content_hash
documents.external_file_id
documents.provider_metadata

chunk_batches.batch_index
chunk_batches.total_chunks

document_chunks.*
table_assets.*
classification label/confidence/raw_response
embedding vector/dimension/token_count
```

---

Và cái này mới là **đúng với flow bạn vừa giải thích**:

```text
             QUEUE = BUFFER / BACKPRESSURE
                       │
                       ▼

Discovery ──→ Download ──→ Extraction ──→ Chunking
   ↑             ↑              ↑             ↑
 Worker N      Worker N        Worker N       Worker N
   │             │              │             │
 batch 1       batch 1         batch 1        batch 1
 batch 2       batch 2         batch 2        batch 2
 batch 3       batch 3         batch 3        batch 3

                         ChunkBatchReady
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Classification     Embedding         Entity
          Queue(N)          Queue(N)          Queue(N)
              │                │                │
              ▼                ▼                ▼
           Result           Result            Result
```

**Các stage vẫn có thứ tự dependency theo batch, nhưng toàn pipeline không tuần tự.** Batch 2 của stage trước hoàn toàn có thể chạy trước batch 1 của stage sau; queue giữ phần việc đang chờ, còn persistence giữ dữ liệu và execution state. Đây chính là Streaming Pipeline mà tài liệu Phase 2 của bạn mô tả. 

Nếu làm **DB-first**, mình sẽ lấy checklist trên làm migration scope; sau đó mới sửa mapper → repository → entity/interface theo đúng DB đã khóa. Import map hiện tại cũng cho thấy rõ các repository cũ đang bị worker chéo gọi, đặc biệt ChunkBatch đang bị cả Chunk, Classification và Embedding dùng chung — đó là phần phải tách ra sau khi DB được sửa.  
