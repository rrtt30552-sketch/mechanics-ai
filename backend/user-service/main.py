from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.api.users import router as users_router

app = FastAPI(title="User Service", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(users_router)


@app.on_event("startup")
async def startup():
    from shared.database import init_db
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "user-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
