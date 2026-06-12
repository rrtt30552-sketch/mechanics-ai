.PHONY: start stop restart status help

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

start: ## 🚀 一键启动 MechAI (后端 + 前端)
	@bash start.sh

stop: ## 🛑 停止所有服务
	@bash stop.sh

restart: ## 🔄 重启所有服务
	@bash stop.sh
	@sleep 1
	@bash start.sh

status: ## 📊 查看服务状态
	@echo "MechAI 服务状态:"
	@curl -s http://localhost:8000/health 2>/dev/null && echo "  ✓ 后端运行中 (port 8000)" || echo "  ✗ 后端未运行"
	@curl -s http://localhost:3000 > /dev/null 2>&1 && echo "  ✓ 前端运行中 (port 3000)" || echo "  ✗ 前端未运行"

dev-backend: ## 🔧 仅启动后端
	python3 server.py

dev-frontend: ## 🎨 仅启动前端
	cd frontend && npm run dev

install: ## 📦 安装所有依赖
	pip install --break-system-packages fastapi uvicorn httpx numpy python-jose passlib bcrypt python-multipart sqlalchemy PyPDF2 python-docx openpyxl python-pptx
	cd frontend && npm install
