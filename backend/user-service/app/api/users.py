from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.database import get_db
from shared.security import verify_token
from shared.exceptions import UnauthorizedException

from app.schemas.user import UserCreate, UserUpdate, UserResponse, Token, LoginRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


async def get_current_user(token: str = Depends(lambda: None), db: AsyncSession = Depends(get_db)):
    """Dependency to get current authenticated user."""
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    # This is a simplified version - see auth middleware below
    pass


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.create_user(data)
    return user


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.authenticate(data.username, data.password)


@router.get("/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db), authorization: str = ""):
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException()
    payload = verify_token(authorization[7:])
    if not payload:
        raise UnauthorizedException()
    svc = UserService(db)
    return await svc.get_user(int(payload["sub"]))


@router.get("/", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.list_users(skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.update_user(user_id, data)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    await svc.delete_user(user_id)
    return {"message": "User deactivated"}
