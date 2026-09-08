from fastapi import FastAPI

from api.ingest import router as ingest_router

from module.chats.chat.presentation.router import (
    router as chat_router,
)


app = FastAPI(
    title="Phantom Force",
)

app.include_router(
    ingest_router,
)
app.include_router(
    chat_router,
)

@app.get("/health")
async def health():
    return {
        "status": "ok",
    }