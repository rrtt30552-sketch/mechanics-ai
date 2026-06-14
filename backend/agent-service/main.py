from fastapi import FastAPI

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.cors import add_cors_middleware
from app.api.chat import router as chat_router

app = FastAPI(title="Agent Service", version="0.3.0")
add_cors_middleware(app)

app.include_router(chat_router)


@app.on_event("startup")
async def startup():
    # Import models so they're registered with SQLAlchemy
    from app.models import chat as chat_models
    # Import User model so FK to users table resolves
    import importlib.util
    user_model_path = os.path.join(os.path.dirname(__file__), '..', 'user-service', 'app', 'models', 'user.py')
    spec = importlib.util.spec_from_file_location("user_model", user_model_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from shared.database import init_db
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
