from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.security import get_password_hash, verify_password, create_access_token
from shared.exceptions import NotFoundException, UnauthorizedException, BadRequestException

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, Token


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        # Check duplicates
        existing = await self.db.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        if existing.scalar_one_or_none():
            raise BadRequestException("Username or email already exists")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> Token:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedException("Account disabled")

        token = create_access_token(user.id, user.username, user.role.value if hasattr(user.role, 'value') else "user")
        return Token(access_token=token)

    async def get_user(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        return user

    async def list_users(self, skip: int = 0, limit: int = 20) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user(user_id)
        user.is_active = False
        await self.db.commit()
