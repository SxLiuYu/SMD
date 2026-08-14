#!/bin/bash
# build-ootb.sh — 从 src/ 构建 OOTB（开箱即用）分发版
# 用法: bash scripts/build-ootb.sh
# 输出: OOTB/ 目录（可用于 git 分发或 zip 打包）

set -euo pipefail
cd "$(dirname "$0")/.."

echo "🔨 构建 OOTB 分发版..."

# 1. 清理旧 OOTB
rm -rf OOTB/charlie
mkdir -p OOTB/charlie

# 2. 复制源码（排除测试、构建产物、敏感文件）
echo "  📦 复制源码..."
rsync -a --exclude='tests/' --exclude='__pycache__/' --exclude='*.pyc' \
      --exclude='.DS_Store' --exclude='data/' --exclude='logs/' \
      --exclude='dist/' --exclude='build/' --exclude='*.spec' \
      --exclude='.env' --exclude='*.token.json' \
      src/ OOTB/charlie/

# 3. 复制 .env.example 和配置文件
cp .env.example OOTB/charlie/
cp -r config/requirements OOTB/charlie/ 2>/dev/null || true
cp config/start.sh OOTB/charlie/ 2>/dev/null || true
cp config/start_tunnel.sh OOTB/charlie/ 2>/dev/null || true
cp config/watchdog.sh OOTB/charlie/ 2>/dev/null || true
cp config/build.sh OOTB/charlie/ 2>/dev/null || true

# 4. 复制文档
cp docs/DEMO_MODE.md OOTB/ 2>/dev/null || true
cp docs/DEPLOYMENT.md OOTB/ 2>/dev/null || true
cp docs/ESP32.md OOTB/ 2>/dev/null || true
cp docs/WINDOWS_BUILD.md OOTB/ 2>/dev/null || true
cp docs/PORTABLE_README.md OOTB/charlie/ 2>/dev/null || true
cp docs/charlie-README.md OOTB/charlie/README.md 2>/dev/null || true

# 5. 复制公开的 skills
rsync -a --exclude='.clawhub/' src/skills/ OOTB/charlie/skills/ 2>/dev/null || true

# 6. 复制 web 前端
cp -r src/web OOTB/charlie/ 2>/dev/null || true

# 7. 创建 OOTB README（如果不存在）
if [ ! -f OOTB/README.md ]; then
  cat > OOTB/README.md << 'EOF'
# Charlie 语音助手 — 开箱即用版 (OOTB)

此目录由 `scripts/build-ootb.sh` 自动生成，请勿手动编辑。

## 快速开始

1. 复制 `.env.example` 为 `.env`，填入 API 密钥
2. `pip install -r requirements.txt`
3. `python voice_server.py`
4. 浏览器访问 http://localhost:8000

## 更多文档

- [Demo 模式](DEMO_MODE.md) — 零配置可用
- [部署指南](DEPLOYMENT.md)
- [ESP32 终端](ESP32.md)
- [Windows 打包](WINDOWS_BUILD.md)
EOF
fi

echo "✅ OOTB 构建完成: $(find OOTB -type f | wc -l | tr -d ' ') 个文件"