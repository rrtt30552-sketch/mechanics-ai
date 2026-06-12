# MechAI - 机械工程 AI 助手平台

面向机械专业学生、教师和工程师的云端机械知识库 AI 助手。

## 🏗️ 项目架构

```
mech-ai/
├── backend/                   # 后端微服务
│   ├── shared/               # 公共库（DB、鉴权、异常）
│   ├── user-service/         # 8001 - 用户管理/JWT/RBAC
│   ├── knowledge-service/    # 8002 - 文档解析/上传/向量检索
│   ├── agent-service/        # 8003 - AI 对话（DeepSeek）
│   ├── ai-service/           # 8004 - AI 能力（embedding/rerank）
│   ├── learning-service/     # 8005 - 学习辅助
│   ├── engineering-service/  # 8006 - 工程辅助
│   ├── diagnosis-service/    # 8007 - 故障诊断
│   ├── rag-service/          # 8008 - RAG 检索链
│   ├── auth-service/         # 8009 - 认证服务
│   └── task-service/         # 8010 - 异步任务
├── frontend/                  # Next.js 前端
├── docker/                   # Nginx 配置
├── docker-compose.yml        # 容器编排
└── .env.example              # 环境变量模板
```

## 🚀 快速开始

### 1. 环境准备

```bash
cp .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY
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

## 📦 核心功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户管理 | ✅ | 注册/登录/JWT/RBAC |
| 文档知识库 | ✅ | PDF/Word/Excel/PPT 解析、上传、检索 |
| AI 问答 | ✅ | DeepSeek 对话、多轮记忆 |
| RAG 检索 | 🔨 | 向量检索 + rerank |
| 学习辅助 | 📋 | 课程辅导、习题生成、考研辅导 |
| 工程辅助 | 📋 | 设计建议、选型、BOM、DFMA/FMEA |
| 故障诊断 | 📋 | 故障分析、维修方案 |

## 🛠️ 技术栈

- **前端**：Next.js 14 + TypeScript + TailwindCSS
- **后端**：Python FastAPI + SQLAlchemy (async)
- **数据库**：PostgreSQL + Milvus (向量) + Redis (缓存)
- **AI**：DeepSeek API + RAG 架构 + sentence-transformers
- **部署**：Docker Compose + Nginx 反向代理

## 📄 License

MIT
