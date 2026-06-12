.PHONY: dev dev-docker stop logs init-db test help

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ===== 本地开发 =====

dev: ## 启动本地开发环境（数据库容器 + 后端/前端本地运行）
	@echo "🔧 启动数据库容器..."
	docker compose up -d postgres redis milvus-standalone minio
	@echo "⏳ 等待数据库就绪..."
	sleep 3
	@echo "✅ 数据库已启动"
	@echo ""
	@echo "请在另一个终端运行以下命令启动后端服务:"
	@echo "  cd backend && export PYTHONPATH=\$$(pwd)"
	@echo "  uvicorn user-service.main:app --port 8001 --reload &"
	@echo "  uvicorn knowledge-service.main:app --port 8002 --reload &"
	@echo "  uvicorn agent-service.main:app --port 8003 --reload &"
	@echo ""
	@echo "请在另一个终端运行以下命令启动前端:"
	@echo "  cd frontend && npm install && npm run dev"
	@echo ""
	@echo "访问: http://localhost:3000"

dev-docker: ## Docker Compose 全部启动
	docker compose up -d --build
	@echo "✅ 所有服务已启动"
	@echo "   前端: http://localhost:3000"
	@echo "   用户服务: http://localhost:8001/docs"
	@echo "   知识服务: http://localhost:8002/docs"
	@echo "   对话服务: http://localhost:8003/docs"
	@echo "   MinIO: http://localhost:9001"

stop: ## 停止所有容器
	docker compose down

logs: ## 查看容器日志
	docker compose logs -f --tail=50

# ===== 数据库 =====

init-db: ## 初始化数据库表
	@echo "创建数据库表..."
	cd backend && python ../scripts/init_db.py

# ===== 测试 =====

test: ## 运行 RAG 测试
	python test_rag.py

# ===== 环境 =====

env: ## 复制 .env.example 到 .env
	@if [ -f .env ]; then echo "⚠️  .env 已存在，跳过"; else cp .env.example .env && echo "✅ 已创建 .env，请编辑填入 DEEPSEEK_API_KEY"; fi
