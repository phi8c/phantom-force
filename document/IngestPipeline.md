Để mình tổng hợp lại theo đúng những gì đã chốt, bỏ hết mấy nhánh lan man.

# 1. Mục tiêu hiện tại

```text
Ưu tiên số 1
=
Làm xong Ingestion Pipeline

Download
↓
Extract
↓
Chunk
↓
Sensitivity (optional)
↓
Embedding
↓
Vector Index
```

Sau khi pipeline chạy end-to-end mới:

```text
Layer First
↓
Module First
```

---

# 2. Chunking đã chốt

## Chunking nhận input

```python
DocumentExtraction
```

---

## Extractor phải trả về cấu trúc chuẩn

Dù là:

```text
Docling
MinerU
Azure Document Intelligence
```

thì cuối cùng đều map về:

```python
{
    "sections": [
        {
            "id": "...",
            "title": "...",
            "level": ...,
            "content": "...",
            "aggregated_content": "...",
            "aggregated_token_count": ...,
            "tables": [],
            "images": [],
            "children": []
        }
    ]
}
```

---

## Auto Chunk

Rule đã chốt:

```text
level >= target_level
AND
token <= max_chunk_tokens
↓
Chunk

token > max_chunk_tokens
AND
có children
↓
Đi xuống child

token > max_chunk_tokens
AND
không còn child
↓
Paragraph Split
```

---

## ParagraphSplitter

Đã thay thế:

```python
ParagraphChunkStrategy
```

bằng:

```python
ParagraphSplitter
```

---

# 3. Không save rồi load lại

Đây là điểm cực kỳ quan trọng.

Sai:

```text
Extract
↓
Save

Load
↓
Chunk

Save

Load
↓
Embedding
```

---

Đúng:

```text
Extract
↓
Chunk
↓
Embedding
↓
Index
```

toàn bộ chạy trong RAM.

---

# 4. Save là Side Effect

Không nằm trên Critical Path.

---

## Luồng chính

```text
Download
↓
Extract
↓
Chunk
↓
Sensitivity
↓
Embedding
↓
Azure Search
```

---

## Luồng phụ

```text
Save Extract

Save Chunk Backup

Audit Log

Metrics
```

---

Có thể:

```python
asyncio.create_task(...)
```

hoặc queue riêng.

---

# 5. Extract Backup

Đã chốt:

```text
Không lưu DB
```

---

Lưu:

```text
Object Storage
```

Ví dụ:

```text
Supabase Storage
Azure Blob
S3
MinIO
R2
```

---

Ví dụ:

```text
extracts/
└── document-id
    └── extract.json
```

---

# 6. Chunk Backup

Đã chốt:

```text
Không lưu PostgreSQL
```

---

Và:

```text
Không xem Vector DB là Source Of Truth
```

---

Chunk sẽ:

```text
Chunk
├── Vector DB
└── Chunk Backup Storage
```

---

Ví dụ:

```text
chunks/
└── document-id
    └── chunks.jsonl
```

---

Lý do:

```text
Đổi Embedding Model
↓
Re-Embed

Không cần Re-Extract
Không cần Re-Chunk
```

---

# 7. AI Profile

Đã chốt.

Một đợt ingest sẽ tham chiếu:

```text
AI Profile
```

---

AI Profile quyết định:

```text
Extract Storage

Chunk Backup Storage

Vector Provider

Embedding Provider
```

---

Ví dụ:

```text
Extract
→ Supabase Storage

Chunk Backup
→ Azure Blob

Embedding
→ Azure OpenAI

Vector
→ Azure Search
```

---

# 8. Các bảng đã chốt

## system.storage_providers

```text
SUPABASE_STORAGE
AZURE_BLOB
S3
MINIO
R2
```

---

## system.vector_providers

```text
AZURE_SEARCH
QDRANT
PGVECTOR
WEAVIATE
PINECONE
```

---

## system.embedding_providers

```text
AZURE_OPENAI
```

---

## ai_profiles

```text
extract_storage_provider_id

chunk_storage_provider_id

vector_provider_id

embedding_provider_id
```

---

## storage_assets

```text
ORIGINAL_FILE
EXTRACT
CHUNK
GRAPH
TABLE_DATA
```

---

# 9. Sensitivity Label

Đây là điểm mới chốt.

---

## Không phải doanh nghiệp nào cũng cần

Nên phải có:

```python
class SensitivityConfiguration:
    enabled: bool
```

---

Ví dụ:

```text
enabled = false
```

thì:

```text
Chunk
↓
Embedding
```

---

Nếu:

```text
enabled = true
```

thì:

```text
Chunk
↓
Sensitivity
↓
Embedding
```

---

# 10. Sensitivity không nên chạy tuần tự

Sai:

```text
Chunk
↓
Label
↓
Embedding
```

---

Đúng:

```text
Chunk
├── Label
└── Embedding
```

chạy song song.

---

# 11. Sensitivity Strategy

Đã chốt:

Không nhét cố định:

```text
10 chunk
20 chunk
50 chunk
```

vào một prompt.

---

Vì:

```text
Chunk size không đồng đều
```

---

Nên cần:

```text
Token Budget Check
```

---

Ví dụ:

```python
max_chunks_per_prompt = 2

max_prompt_tokens = 4000

concurrency = 10
```

---

Worker sẽ:

```text
Chunk
↓
Token Counter
↓
Batch Builder
↓
LLM
```

---

Chunk lớn:

```text
1 chunk / prompt
```

---

Chunk nhỏ:

```text
2 chunk / prompt
```

---

# 12. Embedding Strategy

Khác Sensitivity.

Embedding API hỗ trợ batch.

Ví dụ:

```text
32 chunks
↓
1 embedding request
```

---

Nên Embedding nên:

```text
Batch lớn
```

---

Sensitivity nên:

```text
Micro Batch
```

---

# 13. Azure Search

Schema tương lai nên có:

```json
{
  "chunk_id": "...",
  "document_id": "...",

  "content": "...",

  "embedding": [...],

  "sensitivity_label": "...",

  "hierarchy_path": "...",

  "metadata": {}
}
```

---

# 14. Module First

Đã chốt:

```text
Chưa làm bây giờ.
```

---

Lý do:

```text
Pipeline chưa chạy end-to-end.
```

---

Kế hoạch:

```text
Xong Ingestion Pipeline
↓
Tối phân tích Module Boundary
↓
Chuyển dần sang Module First
```

---

# 15. Việc tiếp theo cần làm ngay

Không phải:

```text
Module Refactor
```

Không phải:

```text
CRUD Configuration
```

---

Mà là:

```text
ExtractWorker
↓
Chunking Engine
↓
Sensitivity Pipeline
↓
Embedding Provider
↓
Azure Search Index
```

Mục tiêu là chạy được:

```text
1 file DOCX
↓
Download
↓
Extract
↓
Chunk
↓
Embedding
↓
Azure Search
```

end-to-end trước. Sau khi vòng này chạy được thì mọi thứ khác (save extract, save chunk, module first, graph...) đều dễ xử lý hơn rất nhiều.
