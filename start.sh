#!/usr/bin/env bash
set -e

# =============================================
#  MechAI 一键启动脚本
#  用法: ./start.sh
# =============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

BACKEND_PORT=8000
FRONTEND_PORT=3000
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo -e "${GREEN}✅ 已停止所有服务${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║          MechAI 启动器 v1.0          ║"
echo "  ║     机械工程 AI 助手平台             ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ----- 检查环境 -----
echo -e "${BLUE}[1/5] 检查运行环境...${NC}"

check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 $(command $1 --version 2>/dev/null | head -1)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 未安装"
        return 1
    fi
}

HAS_ERROR=false
check_cmd python3 || { echo -e "  ${RED}请安装 Python 3.8+${NC}"; HAS_ERROR=true; }
check_cmd node    || { echo -e "  ${RED}请安装 Node.js 16+${NC}"; HAS_ERROR=true; }
check_cmd npm     || { echo -e "  ${RED}请安装 npm${NC}"; HAS_ERROR=true; }

if $HAS_ERROR; then
    echo -e "\n${RED}缺少必要依赖，请先安装后重试${NC}"
    exit 1
fi

# ----- 安装 Python 依赖 -----
echo -e "\n${BLUE}[2/5] 安装 Python 依赖...${NC}"
PYTHON_DEPS="fastapi uvicorn httpx numpy python-jose passlib bcrypt python-multipart sqlalchemy PyPDF2 python-docx openpyxl python-pptx"

# 检查是否已安装
if python3 -c "import fastapi, uvicorn, httpx" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Python 依赖已就绪"
else
    echo -e "  ${YELLOW}⏳ 正在安装...${NC}"
    pip install --break-system-packages -q $PYTHON_DEPS 2>/dev/null || \
    pip install -q $PYTHON_DEPS 2>/dev/null || \
    pip3 install -q $PYTHON_DEPS 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Python 依赖安装完成"
fi

# ----- 安装 Node 依赖 -----
echo -e "\n${BLUE}[3/5] 安装前端依赖...${NC}"
if [ -d "frontend/node_modules" ]; then
    echo -e "  ${GREEN}✓${NC} node_modules 已存在"
else
    echo -e "  ${YELLOW}⏳ 正在安装 (首次需要几分钟)...${NC}"
    cd frontend && npm install --silent && cd ..
    echo -e "  ${GREEN}✓${NC} 前端依赖安装完成"
fi

# ----- 检查端口 -----
echo -e "\n${BLUE}[4/5] 检查端口...${NC}"
for port in $BACKEND_PORT $FRONTEND_PORT; do
    if lsof -i :$port -sTCP:LISTEN &>/dev/null; then
        echo -e "  ${YELLOW}⚠️  端口 $port 已被占用，尝试释放...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    echo -e "  ${GREEN}✓${NC} 端口 $port 可用"
done

# ----- 启动服务 -----
echo -e "\n${BLUE}[5/5] 启动服务...${NC}"

# 启动后端
echo -e "  ${CYAN}▶${NC} 启动后端 (port $BACKEND_PORT)..."
python3 server.py > /tmp/mechai-backend.log 2>&1 &
PIDS+=($!)
sleep 2

# 检查后端是否启动成功
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 后端启动成功"
else
    echo -e "  ${RED}✗${NC} 后端启动失败，查看日志: /tmp/mechai-backend.log"
    cat /tmp/mechai-backend.log
    exit 1
fi

# 启动前端
echo -e "  ${CYAN}▶${NC} 启动前端 (port $FRONTEND_PORT)..."
cd frontend
npm run dev > /tmp/mechai-frontend.log 2>&1 &
PIDS+=($!)
cd ..
sleep 3

# 检查前端是否启动成功
if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 前端启动成功"
else
    echo -e "  ${YELLOW}⏳${NC} 前端正在启动中... (可能需要几秒)"
fi

# ----- 完成 -----
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║         ✅ MechAI 已启动!            ║"
echo "  ╠══════════════════════════════════════╣"
echo "  ║                                      ║"
echo "  ║   🌐 前端: http://localhost:3000      ║"
echo "  ║   🔧 后端: http://localhost:8000      ║"
echo "  ║   📖 API:  http://localhost:8000/docs ║"
echo "  ║                                      ║"
echo "  ║   按 Ctrl+C 停止所有服务             ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# 尝试打开浏览器 (macOS / Linux desktop)
if command -v open &>/dev/null; then
    open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
fi

# 保持前台运行
echo -e "${YELLOW}日志文件: /tmp/mechai-backend.log, /tmp/mechai-frontend.log${NC}"
echo ""
wait
