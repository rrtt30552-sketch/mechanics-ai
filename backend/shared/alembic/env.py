"""
Alembic env.py — 支持 PostgreSQL 异步迁移
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 添加 backend 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import Base

# 导入所有 model 以注册到 metadata（Alembic autogenerate 需要）
# 各 service 目录名含连字符（如 user-service），不能直接作为 Python 包
# 且它们都有同名的 app/ 子包，需要逐个加入 sys.path 并清除缓存后导入
import importlib, glob, os as _os

_backend_dir = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
_model_files = glob.glob(_os.path.join(_backend_dir, '*', 'app', 'models', '*.py'))
_model_files = [f for f in _model_files if not f.endswith('__init__.py')]

for models_file in _model_files:
    service_dir = _os.path.dirname(_os.path.dirname(_os.path.dirname(models_file)))
    mod_name = 'app.models.' + _os.path.splitext(_os.path.basename(models_file))[0]
    # 清除已缓存的 app 模块，避免同名包冲突
    cached = [k for k in sys.modules if k == 'app' or k.startswith('app.')]
    for k in cached:
        del sys.modules[k]
    sys.path.insert(0, service_dir)
    try:
        importlib.import_module(mod_name)
    except Exception:
        pass
    sys.path.remove(service_dir)

config = context.config

# 从环境变量覆盖数据库 URL
db_url = os.getenv("DATABASE_URL", "")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
