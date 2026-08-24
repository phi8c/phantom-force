Oke. Mình chốt lại cục này như sau.

## 1. Orchestration nên là một cục riêng trong Ingest

Mình **không tách nó thành một module/platform độc lập**, vì phạm vi của nó chính là ingest.

Kiến trúc sẽ kiểu:

```text
Ingest
├── Discovery
│
├── Orchestration
│   ├── task management
│   ├── progress tracking
│   ├── retry
│   ├── scheduling/dispatch
│   └── run management
│
├── Queue abstraction
│
└── Processing
    ├── Download
    ├── Extract
    ├── Chunk
    ├── Embed
    ├── Graph
    └── ...
```

**Orchestration là control plane của Ingest.**

Nó biết:

```text
Ingestion Run #123
    ↓
10,000 files
    ↓
file/task nào pending
file/task nào processing
file/task nào completed
file/task nào failed
file/task nào retry
```

Nhưng nó **không tự xử lý file**.

---

## 2. Queue là data-plane transport

Ví dụ:

```text
Orchestration
      ↓
   Queue
      ↓
Download Workers
```

Orchestration quyết định:

> "Task nào cần chạy?"

Queue chịu trách nhiệm:

> "Đưa task đó tới worker nào."

Worker chịu trách nhiệm:

> "Làm task."

Đây là separation rất đẹp cho scale.

Sau này:

```text
Azure Service Bus
RabbitMQ
SQS
Kafka
Redis Queue
...
```

có thể là provider.

Nhưng **queue abstraction/provider chưa nằm trong scope refactor hiện tại**, chỉ thiết kế contract để sau này cắm được.

Và tương tự, nếu một ngày nào đó cần Event Bus thì cũng là một provider/capability riêng. **Không đưa event vào core orchestration bây giờ.**

---

# 3. Orchestration có kiểm soát được 2–3 server không?

Có, **nếu state của nó nằm ở shared persistence**, chứ không nằm trong memory của một server.

Ví dụ:

```text
                 ┌── Server 1
                 │
Orchestration ───┼── Server 2
                 │
                 └── Server 3
                       │
                       ▼
                    Database
                       +
                     Queue
```

Server nào cũng có thể chạy orchestration worker.

DB giữ:

```text
task state
run state
attempt
retry count
timestamps
...
```

Queue giữ task đang chờ xử lý.

Vậy scale ngang không phụ thuộc vào một process duy nhất.

---

# 4. Còn câu hỏi rất hay: "đã sync metadata về DB rồi, có cần Download không?"

**Có.**

Sync về DB và download là **hai chuyện hoàn toàn khác nhau**.

DB chỉ có:

```text
File
├── id
├── external_id
├── name
├── path
├── size
├── content_version
├── metadata
└── ingestion_status
```

Nó **không có nội dung file**.

Muốn:

```text
PDF
 → parse
 → extract text
 → chunk
 → embedding
 → entity extraction
```

thì phải có **content**.

---

# 5. Nhưng Download không nhất thiết có nghĩa "tải về server local"

Đây là điểm mình nghĩ chúng ta nên thiết kế ngay từ đầu.

Ta cần một abstraction kiểu:

```text
Data Hub
    ↓
Download / Content Access
    ↓
Storage
    ↓
Extraction
```

Storage có thể là:

```text
Azure Blob
S3
MinIO
local filesystem
...
```

Và đây lại là **provider**.

Ví dụ doanh nghiệp dùng:

```text
SharePoint
+
Azure Blob Storage
```

thì:

```text
SharePoint
   ↓
Download Worker
   ↓
Azure Blob
   ↓
Extraction Worker
```

Nếu doanh nghiệp dùng:

```text
S3
+
MinIO
```

thì:

```text
S3
   ↓
Download Worker
   ↓
MinIO
   ↓
Extraction Worker
```

---

# 6. Tại sao nên có intermediate storage?

Vì Discovery chỉ biết:

> File này tồn tại.

Download biết:

> Lấy content của file này.

Extraction biết:

> Đọc content này.

Nếu Extraction trực tiếp gọi SharePoint/S3/MinIO thì các module lại biết Data Hub.

**Mất nguyên tắc module độc lập mà bạn vừa chốt.**

Nên:

```text
             Data Hub
                │
                ▼
          Download Worker
                │
                ▼
        Content Storage
                │
                ▼
        Extraction Worker
```

Extraction **không cần biết file đến từ SharePoint hay S3**.

Nó chỉ biết:

```text
content_ref
```

---

## 7. Nhưng Storage này cũng không nên hardcode

Đây là chỗ sau này ta có thể có:

```text
ContentStorageProvider
```

với:

```text
AzureBlobStorage
S3Storage
MinIOStorage
...
```

Và doanh nghiệp cấu hình:

```text
content_storage = azure_blob
```

Core ingest không quan tâm.

---

# 8. Như vậy toàn bộ ingest bắt đầu có hình rất rõ

```text
                    ┌─────────────────┐
                    │   Data Hub      │
                    │ SharePoint/S3…  │
                    └────────┬────────┘
                             │
                         Discovery
                             │
                             ▼
                    ┌─────────────────┐
                    │  Platform DB    │
                    │ Inventory       │
                    └────────┬────────┘
                             │
                    Orchestration
                             │
                             ▼
                          Queue
                             │
                             ▼
                       Download
                             │
                             ▼
                    Content Storage
                             │
                             ▼
                        Extract
                             │
                             ▼
                         Chunk
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                  Embed            Graph
```

Và mỗi cục có thể scale worker độc lập:

```text
Discovery      × N
Download       × N
Extraction     × N
Chunking       × N
Embedding      × N
Graph          × N
```

**Orchestration đứng bên trên để quản lý task/run/progress/retry; Queue đứng giữa để phân phối work.**

Đây là hướng mình nghĩ rất hợp với mục tiêu ban đầu của bạn: **scale theo số lượng file và không để Data Hub-specific code lan vào các module khác.**

Còn **Storage cục này** mình nghĩ nên bàn riêng sau Discovery + Orchestration, vì nó liên quan trực tiếp tới lifecycle của downloaded content, retention, cleanup, retry và việc Extract worker lấy content như thế nào.
