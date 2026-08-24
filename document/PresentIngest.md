Được, trước khi sửa bug thì phải khóa lại kiến trúc. Không thì lại rơi đúng tình trạng mấy hôm nay:

```text
Sửa file A đúng
↓
File B lệch
↓
Sửa file B
↓
File C lệch
↓
Quay lại file A
```

vì không có một "source of truth" cho ingest.

---

# 1. Mục tiêu thật sự của hệ thống

Người dùng chọn:

```text
Site
Folder
SubFolder
File
```

---

Traversal trả về:

```python
list[DiscoveredFile]
```

Ví dụ:

```text
A.docx
B.docx
C.pdf
...
```

---

Sau đó hệ thống phải:

```text
Download
↓
Extract
↓
Chunk
↓
Classify
↓
Embed
↓
Index
```

cho từng file.

---

# 2. Download là bottleneck lớn nhất

Giả sử:

```text
5 file
```

thì:

```text
download trực tiếp
```

cũng được.

---

Nhưng:

```text
1000 file
5000 file
10000 file
```

thì:

```python
for file in files:
    await download(file)
```

là chết.

---

Nên Download phải là stage có khả năng scale mạnh nhất.

---

# 3. Download Architecture

Traversal:

```text
List<File>
```

↓

Register Documents

↓

Create Download Tasks

↓

Dispatch Download Tasks

↓

Download Queue

↓

Download Workers

↓

Download File

↓

Temp File

↓

DocumentDownloadedEvent

---

Ví dụ:

```text
5000 files
```

↓

```text
5000 download tasks
```

↓

```text
Azure Service Bus
```

↓

```text
20 download workers
```

cùng xử lý.

---

# 4. Event Driven là Business Flow

Đây là điểm rất quan trọng.

Sai:

```text
Azure Service Bus
=
Business Flow
```

---

Đúng:

```text
Business Flow
=
Event
```

---

Azure Service Bus chỉ là:

```text
Execution Topology
```

theo đúng định hướng ingest đã chốt. 

---

# 5. Event Flow chuẩn

Download xong:

```python
DocumentDownloadedEvent
```

---

Fan-out:

```text
ExtractHandler
```

---

Extract xong:

```python
DocumentExtractedEvent
```

---

Fan-out:

```text
SaveExtractionHandler
ChunkHandler
```

---

Hai nhánh này chạy song song.

Theo định hướng:

```text
Lưu dữ liệu
và
xử lý tiếp

không được chặn nhau
```



---

# 6. Chunk Phase

ChunkHandler:

```python
DocumentExtractedEvent
↓
ChunkingEngine
↓
ChunkCreatedEvent
```

---

ChunkCreatedEvent không được index ngay.

Đây là chỗ quan trọng nhất.

Theo tài liệu ingest:

```text
ChunkCreatedEvent
không được lưu Azure Search
```



---

# 7. ChunkCreatedEvent Fan-Out

Khi:

```python
ChunkCreatedEvent
```

xuất hiện.

Nó phải fan-out:

```text
ChunkCreatedStateHandler
ClassifyHandler
EmbedHandler
```

đồng thời.

---

Không phải:

```text
Chunk
↓
Classify
↓
Embed
```

---

Mà là:

```text
Chunk
├── State
├── Classification
└── Embedding
```

---

# 8. State dùng để làm gì?

Vấn đề:

```text
Classification
và
Embedding
```

chạy độc lập.

---

Không ai biết:

```text
thằng nào xong trước
```

---

Nên cần:

```python
DocumentPipelineState
```

để đồng bộ.

---

State giữ:

```python
chunks
labels
embeddings

chunks_ready
classification_ready
embedding_ready

index_event_published
```

---

Mục tiêu:

```text
gom dữ liệu
từ nhiều nhánh
```

---

# 9. Classification Completed

```python
ClassificationCompletedEvent
```

↓

```text
state.labels = ...
state.classification_ready = True
```

---

Sau đó kiểm tra:

```python
classification_ready
and
embedding_ready
```

---

Nếu chưa:

```text
đợi
```

---

# 10. Embedding Completed

```python
EmbeddingCompletedEvent
```

↓

```text
state.embeddings = ...
state.embedding_ready = True
```

---

Sau đó kiểm tra:

```python
classification_ready
and
embedding_ready
```

---

Nếu đủ:

```python
DocumentReadyForIndexEvent
```

---

# 11. Điểm hợp nhất cuối cùng

Theo tài liệu:

```text
DocumentReadyForIndexEvent
=
điểm hợp nhất cuối cùng
```



---

Lúc này mới có:

```text
Chunk Content
+
Labels
+
Embeddings
```

đầy đủ.

---

# 12. Index Phase

```python
DocumentReadyForIndexHandler
```

↓

```text
Azure Search
```

↓

```text
Supabase Backup
```

---

Đây mới là lần lưu chính thức.

Theo định hướng ingest:

```text
Không lưu chunk trước
Không update lại sau

Chỉ index một lần
```



---

# 13. Azure Service Bus nằm ở đâu?

Nó KHÔNG nằm trong:

```text
DocumentDownloadedEvent
DocumentExtractedEvent
ChunkCreatedEvent
```

---

Nó nằm ở:

```text
DOWNLOAD_QUEUE

EXTRACT_QUEUE

CHUNK_QUEUE

EMBED_QUEUE

CLASSIFY_QUEUE

INDEX_QUEUE
```



---

Ví dụ:

```text
ChunkCreatedEvent
```

có thể:

```text
Local Mode
```

↓

```python
EventDispatcher
```

---

hoặc:

```text
Azure Mode
```

↓

```python
AzureServiceBusEventBus
```

↓

```text
CHUNK_QUEUE
```

↓

```text
ChunkWorker
```

---

Business Flow không đổi.

---

# 14. Kết luận

Luồng ingest đã chốt hiện tại là:

```text
User Select Site/Folder/SubFolder/File
↓
Traversal

↓
List<File>

↓
Register Documents

↓
Create Download Tasks

↓
DOWNLOAD_QUEUE

↓
DownloadWorker

↓
Download File

↓
Temp File

↓
DocumentDownloadedEvent

══════════════════════════

ExtractHandler

↓
DocumentExtractedEvent

├── SaveExtractionHandler
└── ChunkHandler

↓
ChunkCreatedEvent

├── ChunkCreatedStateHandler
├── ClassifyHandler
└── EmbedHandler

↓

ClassificationCompletedEvent
EmbeddingCompletedEvent

↓

DocumentReadyForIndexEvent

↓

DocumentReadyForIndexHandler

↓

Azure Search
+
Supabase Backup
```

Nếu lấy đây làm "luật", thì giờ mới bắt đầu đi tìm bug xem chỗ nào trong code hiện tại đang lệch khỏi flow này. Đây là thứ mình sẽ đối chiếu trước khi sửa bất kỳ file nào tiếp theo.
