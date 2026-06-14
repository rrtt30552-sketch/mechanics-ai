"""
共享 CORS 配置
统一管理跨域策略，避免各服务重复配置
"""
import os
from fastapi.middleware.cors import CORSMiddleware


def get_cors_origins() -> list[str]:
    """获取允许的 CORS 来源"""
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]

    # 开发环境默认值
    return [
        "http://localhost:3000",
        "http://localhost:80",
        "http://127.0.0.1:3000",
    ]


def add_cors_middleware(app):
    """为 FastAPI 应用添加 CORS 中间件"""
    origins = get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
