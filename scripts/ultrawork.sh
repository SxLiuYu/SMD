#!/bin/bash
# ultrawork.sh - 在 DSH 中启动 ultrawork 模拟
# 用法: ./ultrawork.sh "任务描述" [项目路径]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${2:-.}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              🚀 ultrawork - DSH 多 Agent 并行执行           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  任务: $1                                              ║"
echo "║  项目: $PROJECT_DIR                                        ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 提示: 在 DSH 中直接说 'ultrawork [任务]' 即可触发此模式"
echo ""
echo "示例:"
echo "  ./ultrawork.sh '重构 voice_agent.py'"
echo "  ./ultrawork.sh '诊断 ASR 模块的 bug'"
echo "  ./ultrawork.sh '实现新的 MCP 技能'"
echo ""
