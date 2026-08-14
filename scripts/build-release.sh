#!/bin/bash
# build-release.sh — OOTB 开箱即用版多平台构建
# 用法: bash scripts/build-release.sh [macos|windows|linux|all]
# 输出: dist/release/<platform>/Charlie-<version>-<platform>.zip
#
# 与 build-custom.sh 的区别：
#   - 不含密钥（用户需自行配置 .env）
#   - 不含 ESP32 定制固件（使用公版固件）
#   - 排除可选模块的敏感依赖
#   - 生成可分发的 ZIP 包

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo 'dev')}"
PLATFORM="${1:-all}"

build_one() {
  local platform="$1"
  local dist_dir="dist/release/$platform"
  local zip_name="Charlie-${VERSION}-${platform}.zip"

  echo "🔨 构建 OOTB 分发版 — $platform"
  echo "   版本: $VERSION"
  echo ""

  # 1. 安装依赖
  echo "[1/4] 安装构建依赖..."
  pip install pyinstaller --quiet 2>/dev/null || true
  pip install -r config/requirements/requirements-core.txt --quiet 2>/dev/null || true

  # 2. 运行测试（仅纯逻辑测试，跳过需要 Opus/LLM/网络的集成测试）
  echo "[2/4] 运行测试..."
  python -m pytest \
    src/tests/test_intent_rules.py \
    src/tests/test_reminders.py \
    src/tests/test_security_fixes.py \
    src/tests/test_state.py \
    src/tests/test_config.py \
    src/tests/test_utils.py \
    src/tests/test_mcp_gate.py \
    -q --tb=short 2>&1 | tail -3 || {
    echo "⚠️ 部分测试失败，继续构建..."
  }

  # 3. 清理旧构建
  echo "[3/4] 清理..."
  rm -rf build/ "$dist_dir"

  # 4. PyInstaller 构建
  echo "[4/4] PyInstaller 构建..."
  pyinstaller config/charlie.spec \
    --distpath "$dist_dir" \
    --workpath build \
    --noconfirm 2>&1 | tail -10

  # 5. 后处理：复制 .env.example（不含密钥）
  if [ -f "$dist_dir/charlie/_internal/.env.example" ]; then
    cp "$dist_dir/charlie/_internal/.env.example" "$dist_dir/charlie/.env.example"
  elif [ -f "$dist_dir/charlie/.env.example" ]; then
    true  # 已在正确位置
  else
    cp .env.example "$dist_dir/charlie/.env.example"
  fi

  # 6. 打包 ZIP
  echo ""
  echo "📦 打包 $zip_name..."
  cd "$dist_dir"
  if [ -d charlie ]; then
    zip -r "$zip_name" charlie/ -x "*.pyc" "__pycache__/*" ".DS_Store" > /dev/null
    SIZE=$(du -sh "$zip_name" | cut -f1)
    echo "✅ OOTB 构建成功: $zip_name ($SIZE)"
  else
    echo "❌ 构建失败: 找不到 charlie/ 目录"
    exit 1
  fi
  cd "$ROOT"
}

case "$PLATFORM" in
  macos|darwin)
    build_one "macos"
    ;;
  windows|win)
    build_one "windows"
    ;;
  linux)
    build_one "linux"
    ;;
  all)
    build_one "macos"
    build_one "windows"
    build_one "linux"
    ;;
  *)
    echo "用法: bash scripts/build-release.sh [macos|windows|linux|all]"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "✅ 构建完成!"
echo "   产物: dist/release/"
echo "=========================================="