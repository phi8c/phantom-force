yourdomain-monorepo/
├── apps/
│   ├── web/                              # app.yourdomain.com — Chat, có phần public cần SEO
│   │   ├── app/
│   │   │   ├── (marketing)/              # SSG/ISR, Metadata API, sitemap.ts
│   │   │   ├── (auth)/                   # login/register/mfa — noindex
│   │   │   ├── (chat)/                   # sau đăng nhập — chat, settings/security cá nhân
│   │   │   └── middleware.ts
│   │   └── next.config.js                # rewrites /api/* → backend nội bộ
│   │
│   └── admin/                            # admin.yourdomain.com — quản trị hệ thống, KHÔNG cần SEO
│       ├── app/
│       │   ├── (auth)/                   # login riêng cho admin, bắt buộc MFA
│       │   ├── (panel)/
│       │   │   ├── users/                # list/lock/unlock user
│       │   │   ├── roles/                # CRUD role + gán permission
│       │   │   ├── policies/             # policy builder (ABAC động)
│       │   │   ├── sources/              # quản lý ingestion source
│       │   │   └── audit-logs/           # xem audit trail
│       │   └── layout.tsx                # robots: noindex toàn bộ
│       │   └── middleware.ts             # check cookie riêng của admin host
│       └── next.config.js
│
├── packages/
│   ├── ui/                               # design system dùng chung (shadcn/ui base)
│   ├── api-client/                       # generate từ OpenAPI schema của FastAPI (openapi-typescript/orval)
│   │                                     # → type-safe, tự động khớp khi BE đổi Pydantic schema
│   ├── auth-client/                      # session helper, CSRF helper — dùng chung logic, KHÔNG dùng chung cookie
│   ├── eslint-config/
│   └── tsconfig/
│
├── turbo.json
└── pnpm-workspace.yaml







module/
│
├── enterprise/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── ...
│
├── knowledge_space/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── ...
│
├── master_data/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── data_hub_provider.py
│   │   ├── enums/
│   │   └── contracts/
│   │       └── data_hub_provider_repository.py
│   │
│   ├── application/
│   │   ├── dtos/
│   │   └── use_cases/
│   │
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── models/
│   │       │   └── data_hub_provider_model.py
│   │       ├── mappers/
│   │       │   └── data_hub_provider_mapper.py
│   │       └── repositories/
│   │           └── data_hub_provider_repository_impl.py
│   │
│   └── ...
│
├── ai/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── ...
│
├── data_platform/
│   └── data_hub/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
│
└── ingest/
    │
    ├── config/
    │   ├── domain/
    │   ├── application/
    │   ├── infrastructure/
    │   └── ...
    │
    └── discovery/
        ├── domain/
        ├── application/
        ├── infrastructure/
        └── worker/







////////////////////////////////////////////////////////////////////////////////////////////




module/
├── enterprise/
│   └── persistence/
│       └── enterprises
│
├── knowledge_space/
│   └── persistence/
│       ├── knowledge_spaces
│       ├── knowledge_space_data_hubs
│       └── knowledge_space_embedding_configs
│
├── data_platform/
│   └── data_hub/
│       └── persistence/
│           └── data_hub_providers
│
├── ai/
│   └── persistence/
│       ├── embedding_models
│       ├── extraction_engines
│       ├── chunking_strategies
│       ├── classification_engines
│       ├── classification_model_sets
│       └── classification_model_set_items
│
└── ingest/
    └── discovery/
        └── persistence/
            ├── documents
            └── ingestion_document_states

        └── ... 
            ingestion_jobs
            ingestion_job_configurations