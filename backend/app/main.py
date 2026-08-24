from fastapi import FastAPI

from app.router.router import (
    api_router,
)

app = FastAPI(
    title="Enterprise RAG Ingestion",
)

app.include_router(
    api_router,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }