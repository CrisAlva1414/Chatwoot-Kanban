from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_pool, init_pool
from app.routers import api, conversations, kanban, webhooks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Chatwoot Integration - i-labs", lifespan=lifespan)

app.include_router(conversations.router)
app.include_router(api.router)
app.include_router(kanban.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
