from fastapi import FastAPI


app = FastAPI(
    title="Phantom Force",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }
