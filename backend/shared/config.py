"""
Configuration - Environment variables
"""
import os
from functools import lru_cache


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/mech_ai")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "mechai-dev-secret-change-in-production")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
