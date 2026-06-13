from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.api.chat import router as chat_router

app = FastAPI(title="Agent Service", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(chat_router)


@app.on_event("startup")
async def startup():
    # Import models so they're registered with SQLAlchemy
    from app.models import chat as chat_models
    from shared.database import init_db
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
