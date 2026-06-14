"""
API Rate Limiting — 基于内存的简单限流
生产环境建议用 Redis 做分布式限流
"""
import time
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException
import os

# 配置
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))

# 内存存储: {client_id: [timestamp, ...]}
_request_log: dict[str, list[float]] = defaultdict(list)


def _get_client_id(request: Request) -> str:
    """获取客户端标识（IP 或 用户 ID）"""
    # 优先用 X-Real-IP（Nginx 代理）
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, limit: Optional[int] = None, window: int = 60):
    """检查是否超过限流"""
    if not RATE_LIMIT_ENABLED:
        return

    limit = limit or RATE_LIMIT_PER_MINUTE
    client_id = _get_client_id(request)
    now = time.time()
    cutoff = now - window

    # 清理过期记录
    _request_log[client_id] = [t for t in _request_log[client_id] if t > cutoff]

    if len(_request_log[client_id]) >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"请求过于频繁，每分钟最多 {limit} 次",
                "retry_after": int(_request_log[client_id][0] + window - now) + 1,
            },
        )

    _request_log[client_id].append(now)


def rate_limit_dependency(request: Request):
    """FastAPI 依赖注入用"""
    check_rate_limit(request)
