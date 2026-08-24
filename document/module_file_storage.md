module/data_platform/file_storage/
│
├── __init__.py
│
├── api/                         # In-process public API
│   ├── __init__.py
│   └── file_storage.py
│
├── composition/                 # Composition/bootstrap
│   ├── __init__.py
│   └── factory.py
│
├── domain/
│   └── contracts/
│       └── file_storage.py
│
├── application/
│   └── services/
│       └── file_storage_service.py
│
├── infrastructure/
│   └── providers/
│       └── supabase/
│           ├── client.py
│           └── file_storage.py
│
└── presentation/
    └── http/                    # HTTP/microservice boundary
        ├── __init__.py
        ├── router.py
        ├── schemas.py
        └── dependencies.py



///////////////////////////////////////////////////////////////////////////////////////






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