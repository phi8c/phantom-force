import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingest import router as ingest_router
from api.ingest_orchestration import (
    router as ingest_orchestration_router,
)
from module.enterprise.presentation.api import (
    router as enterprise_router,
)
from module.ai.embedding_model.presentation.router import (
    router as embedding_model_router,
)
from module.master_data.data_hub_providers.presentation.router import (
    router as data_hub_provider_router,
)
from module.knowledge_space.presentation.router import (
    router as knowledge_space_router,
)
from module.ingest.master.presentation.router import (
    router as ingest_master_router,
)
from module.data_platform.common.microsoft_graph.authentication.factory import (
    create_graph_token_provider,
)
from module.data_platform.data_hub.sharepoint.presentation.http.dependencies import (
    build_data_hub_service,
)
from module.data_platform.data_hub.sharepoint.presentation.http.router import (
    get_data_hub_service,
)
from module.data_platform.data_hub.sharepoint.presentation.http.router import (
    router as data_hub_router,
)

from module.chats.chat.presentation.router import (
    router as chat_router,
)


app = FastAPI(
    title="Phantom Force",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://192.168.1.18:3000,http://192.168.1.18:3001",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    ingest_router,
)
app.include_router(
    ingest_orchestration_router,
)
app.include_router(
    ingest_master_router,
)
app.include_router(
    enterprise_router,
)
app.include_router(
    data_hub_provider_router,
)
app.include_router(
    data_hub_router,
)
app.include_router(
    embedding_model_router,
)
app.include_router(
    knowledge_space_router,
)
app.include_router(
    chat_router,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


def _build_runtime_data_hub_service():
    return build_data_hub_service(
        token_provider=create_graph_token_provider(),
    )


app.dependency_overrides[get_data_hub_service] = (
    _build_runtime_data_hub_service
)
