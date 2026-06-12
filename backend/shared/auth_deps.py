"""
认证依赖 — 从 JWT token 提取当前用户
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import get_db
from shared.security import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    从 JWT token 中提取 user_id
    用法: user_id: int = Depends(get_current_user_id)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先登录",
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期，请重新登录",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式错误",
        )

    return int(user_id)


async def get_current_user_id_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int | None:
    """
    可选认证 — 未登录返回 None
    用法: user_id: int | None = Depends(get_current_user_id_optional)
    """
    if not credentials:
        return None

    payload = verify_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    return int(user_id) if user_id else None
