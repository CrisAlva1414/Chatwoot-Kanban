from fastapi import FastAPI

from app.routers import conversations

app = FastAPI(title="Chatwoot Integration - i-labs")

app.include_router(conversations.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
