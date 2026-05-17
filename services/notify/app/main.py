import asyncio
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.consumer import start_consumer

# Force stdout to flush immediately so logs appear in docker
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_consumer())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Notify Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notify"}