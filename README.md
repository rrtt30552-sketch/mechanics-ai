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

## 🚀 一键启动

**前置要求：** Python 3.8+ 和 Node.js 16+

```bash
# 克隆仓库
git clone -b dev https://github.com/rrtt30552-sketch/mechanics-ai.git
cd mechanics-ai

# 一键启动！
./start.sh
```

启动后自动打开 http://localhost:3000 即可使用。

**其他命令：**
```bash
make start    # 启动
make stop     # 停止
make restart  # 重启
make status   # 查看状态
```

## 📦 核心功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户管理 | ✅ | 注册/登录/JWT/RBAC |
| 文档知识库 | ✅ | PDF/Word/Excel/PPT 解析、上传、检索 |
| AI 问答 | ✅ | DeepSeek 对话、SSE 流式、多轮记忆 |
| RAG 检索 | ✅ | TF-IDF 本地向量检索 |
| 学习辅助 | ✅ | 课程辅导、习题生成、考研辅导、错题分析 |
| 工程辅助 | ✅ | 设计建议、选型计算、BOM、工艺路线、DFMA、FMEA |
| 故障诊断 | 📋 | 故障分析、维修方案 |

## 🛠️ 技术栈

- **前端**：Next.js 14 + TypeScript + TailwindCSS
- **后端**：Python FastAPI + SQLAlchemy (async)
- **数据库**：PostgreSQL + Milvus (向量) + Redis (缓存)
- **AI**：DeepSeek API + RAG 架构 + sentence-transformers
- **部署**：Docker Compose + Nginx 反向代理

## 📄 License

MIT
