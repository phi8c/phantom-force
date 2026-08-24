modules/
└── memory/
    ├── __init__.py
    │
    ├── migrations/                            # ⭐ NGUỒN SỰ THẬT (DB-first) — viết tay trước tiên
    │   ├── 0001_create_memory_buffer.sql
    │   ├── 0002_create_episodic_memory.sql     # bật pgvector extension tại đây
    │   ├── 0003_create_user_profile.sql
    │   ├── 0004_create_session_summary.sql
    │   └── README.md                           # quy ước đặt tên, thứ tự chạy, cách rollback
    │
    ├── domain/                                # Entity ánh xạ THEO schema đã migrate, không sinh ngược
    │   ├── __init__.py
    │   ├── entities/
    │   │   ├── __init__.py
    │   │   ├── memory_buffer.py               # field khớp 1-1 với bảng memory_buffer
    │   │   ├── session_summary.py             # khớp bảng session_summary
    │   │   ├── episodic_memory.py             # khớp bảng episodic_memory (+ pgvector column)
    │   │   └── user_profile.py                # khớp bảng user_profile
    │   │
    │   ├── value_objects/
    │   │   ├── __init__.py
    │   │   ├── memory_operation.py            # Enum: ADD / UPDATE / DELETE / NOOP
    │   │   ├── importance_score.py
    │   │   ├── retrieval_score.py
    │   │   └── memory_type.py
    │   │
    │   ├── ports/
    │   │   ├── __init__.py
    │   │   ├── memory_reader_port.py
    │   │   ├── memory_writer_port.py
    │   │   ├── summarizer_port.py
    │   │   ├── embedding_port.py
    │   │   └── extraction_port.py
    │   │
    │   └── exceptions/
    │       ├── __init__.py
    │       └── memory_exceptions.py
    │
    ├── application/
    │   ├── __init__.py
    │   ├── use_cases/
    │   │   ├── __init__.py
    │   │   ├── append_to_buffer.py
    │   │   ├── summarize_session.py
    │   │   ├── extract_candidate_facts.py
    │   │   ├── consolidate_memory.py
    │   │   ├── retrieve_relevant_memory.py
    │   │   ├── get_user_profile.py
    │   │   └── prune_expired_memory.py
    │   │
    │   ├── dto/
    │   │   ├── __init__.py
    │   │   ├── memory_query_dto.py
    │   │   ├── candidate_fact_dto.py
    │   │   └── retrieval_result_dto.py
    │   │
    │   └── services/
    │       ├── __init__.py
    │       ├── relevance_ranker.py
    │       └── dedup_resolver.py
    │
    ├── infrastructure/
    │   ├── __init__.py
    │   ├── repositories/                      # Query trực tiếp map theo schema đã có sẵn trong DB
    │   │   ├── __init__.py
    │   │   ├── supabase_buffer_repository.py
    │   │   ├── supabase_episodic_repository.py
    │   │   ├── supabase_profile_repository.py
    │   │   └── supabase_summary_repository.py
    │   │
    │   ├── embedding/
    │   │   ├── __init__.py
    │   │   └── openai_embedding_adapter.py
    │   │
    │   ├── extraction/
    │   │   ├── __init__.py
    │   │   ├── llm_fact_extractor.py
    │   │   └── prompts/
    │   │       ├── extract_facts.prompt.md
    │   │       └── consolidate_decision.prompt.md
    │   │
    │   ├── summarization/
    │   │   ├── __init__.py
    │   │   └── llm_summarizer.py
    │   │
    │   └── jobs/
    │       ├── __init__.py
    │       ├── prune_job.py
    │       └── scheduler.py
    │
    ├── interface/
    │   ├── __init__.py
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── router.py
    │   │   └── schemas.py
    │   │
    │   └── di/
    │       ├── __init__.py
    │       └── container.py
    │
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    │
    └── tests/
        ├── unit/
        │   ├── test_consolidate_memory.py
        │   ├── test_relevance_ranker.py
        │   └── test_dedup_resolver.py
        └── integration/
            ├── test_supabase_episodic_repository.py
            └── test_retrieve_relevant_memory.py