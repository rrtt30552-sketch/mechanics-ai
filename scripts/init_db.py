#!/usr/bin/env python3
"""
数据库初始化脚本 — 创建所有表
运行方式: cd backend && python ../scripts/init_db.py
"""
import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

# Register shared package
import types
shared_pkg = types.ModuleType('shared')
shared_pkg.__path__ = [os.path.join(backend_dir, 'shared')]
sys.modules['shared'] = shared_pkg

# Now import
from shared.database import Base, engine

# Import all models
sys.path.insert(0, os.path.join(backend_dir, 'user-service'))
sys.path.insert(0, os.path.join(backend_dir, 'knowledge-service'))
sys.path.insert(0, os.path.join(backend_dir, 'agent-service'))

from app.models.user import User  # noqa
from app.models.document import Document, DocumentChunk  # noqa
from app.models.chat import Conversation, Message  # noqa


def init_db():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    print(f"\nTables: {', '.join(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    init_db()
