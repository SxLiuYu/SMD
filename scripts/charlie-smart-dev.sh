#!/bin/bash
# charlie-smart-dev.sh - Charlie 智能开发系统快捷入口
# 
# 用法: ./charlie-smart-dev.sh "<需求描述>"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           🧠 Charlie 智能开发系统                           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                          ║
echo "║  正在分析需求...                                          ║"
echo "║                                                          ║
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_DIR"
node scripts/charlie-smart-dev.js "$@"
