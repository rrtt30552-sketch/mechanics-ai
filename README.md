# MechAI - 机械工程 AI 助手平台

面向机械专业学生、教师和工程师的云端机械知识库 AI 助手。

## 🏗️ 项目架构

```
mechanics-ai/
├── backend/                   # 后端微服务
│   ├── shared/               # 公共库（DB、鉴权、异常、RAG、LLM）
│   │   ├── alembic/          # 数据库迁移脚本
│   │   ├── config.py         # 环境变量配置
│   │   ├── cors.py           # 共享 CORS 配置
│   │   ├── database.py       # SQLAlchemy 异步引擎
│   │   ├── embedding.py      # 文本向量化（sentence-transformers / TF-IDF）
│   │   ├── exceptions.py     # 自定义异常
│   │   ├── llm.py            # 多模型 LLM 客户端
│   │   ├── rag.py            # RAG 检索服务
│   │   ├── rate_limit.py     # API 限流
│   │   ├── security.py       # JWT + 密码哈希
│   │   └── requirements.txt  # Python 依赖
│   ├── user-service/         # 8001 - 用户管理/JWT/RBAC
│   ├── knowledge-service/    # 8002 - 文档解析/上传/向量检索
│   ├── agent-service/        # 8003 - AI 对话（多模型）
│   ├── learning-service/     # 8005 - 学习辅助
│   ├── engineering-service/  # 8006 - 工程辅助
│   ├── diagnosis-service/    # 8007 - 故障诊断
│   ├── tests/                # 单元测试
│   └── Dockerfile.service    # 后端统一 Docker 镜像
├── frontend/                  # Next.js 14 前端
├── docker/                   # Nginx 配置
├── .github/workflows/        # CI/CD
├── docker-compose.yml        # 容器编排
├── .env.example              # 环境变量模板
└── test_rag.py               # RAG 端到端测试
```

## 🚀 快速开始

### 1. 环境准备

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key（至少一个）
# 推荐: DEEPSEEK_API_KEY 或 MIMO_API_KEY
```

### 2. Docker Compose 启动

```bash
docker-compose up -d
```

启动后访问：
- 前端：http://localhost:3000
- 用户服务：http://localhost:8001/docs
- 知识服务：http://localhost:8002/docs
- 对话服务：http://localhost:8003/docs
- MinIO 控制台：http://localhost:9001

### 3. 本地开发

```bash
# 后端
cd backend
pip install -r shared/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
export PYTHONPATH=$(pwd)
uvicorn user-service.main:app --port 8001 --reload

# 前端
cd frontend
npm install
npm run dev
```

### 4. 数据库迁移

```bash
cd backend
export PYTHONPATH=$(pwd)

# 初始化 Alembic（首次）
alembic -c shared/alembic.ini revision --autogenerate -m "init"

# 执行迁移
alembic -c shared/alembic.ini upgrade head

# 回滚
alembic -c shared/alembic.ini downgrade -1
```

## 📦 核心功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户管理 | ✅ | 注册/登录/JWT/PBKDF2 密码加密 |
| 文档知识库 | ✅ | PDF/Word/Excel/PPT 解析、上传、向量检索 |
| AI 问答 | ✅ | 多模型对话（MiMo/DeepSeek/Qwen）、流式输出、多轮记忆 |
| RAG 检索 | ✅ | pgvector 生产 + JSON 文件本地开发 |
| 学习辅助 | ✅ | 课程辅导、习题生成、考研辅导、错题分析 |
| 工程辅助 | ✅ | 设计建议、选型计算、BOM、DFMA/FMEA |
| 故障诊断 | ✅ | 故障分析、振动分析、磨损分析、维护计划 |
| API 限流 | ✅ | 内存限流（可扩展为 Redis） |
| 数据库迁移 | ✅ | Alembic 异步迁移 |
| CI/CD | ✅ | GitHub Actions (lint + test + docker build) |

## 🛠️ 技术栈

- **前端**：Next.js 14 + TypeScript + TailwindCSS
- **后端**：Python FastAPI + SQLAlchemy (async)
- **数据库**：PostgreSQL + pgvector (向量) + Redis (缓存)
- **AI**：MiMo / DeepSeek / Qwen + RAG 架构 + sentence-transformers
- **部署**：Docker Compose + Nginx 反向代理
- **CI**：GitHub Actions

## 🔒 安全特性

- JWT 认证 + PBKDF2-SHA256 密码哈希
- 生产环境强制校验 JWT_SECRET
- SQL 参数化查询（防注入）
- API 限流（防刷）
- CORS 白名单配置

## 📄 License

MIT
