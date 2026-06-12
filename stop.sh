#!/usr/bin/env bash
echo "正在停止 MechAI..."
pkill -f "python3 server.py" 2>/dev/null && echo "  ✓ 后端已停止" || echo "  - 后端未在运行"
pkill -f "next dev" 2>/dev/null && echo "  ✓ 前端已停止" || echo "  - 前端未在运行"
pkill -f "node.*next" 2>/dev/null && true
echo "✅ MechAI 已停止"
