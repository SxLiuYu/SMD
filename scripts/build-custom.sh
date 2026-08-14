#!/bin/bash
# build-custom.sh — 自用定制版构建（CUSTOM，含密钥配置）
# 用法: bash scripts/build-custom.sh [macos|windows|linux]
# 输出: dist/custom/<platform>/
#
# 与 build-ootb.sh 的区别：
#   - 包含 .env 中的真实密钥（仅限本地使用，不分发）
#   - 包含 ESP32 定制固件配置
#   - 不排除任何可选模块

set -euo pipefail
cd "$(dirname "$0")/.."

PLATFORM="${1:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
case "$PLATFORM" in
  darwin|macos|mac)  PLATFORM="macos" ;;
  windows|win)       PLATFORM="windows" ;;
  linux)             PLATFORM="linux" ;;
  *) echo "不支持的平台: $PLATFORM"; exit 1 ;;
esac

DIST_DIR="dist/custom/$PLATFORM"
echo "🔨 构建 CUSTOM 自用版 — $PLATFORM"
echo "   输出: $DIST_DIR"
echo ""

# 1. 激活虚拟环境
if [ -f charlie/.venv/bin/activate ]; then
  source charlie/.venv/bin/activate
fi

# 2. 安装依赖
echo "[1/5] 安装构建依赖..."
pip install pyinstaller --quiet 2>/dev/null || true
pip install -r config/requirements/requirements.txt --quiet 2>/dev/null || true

# 3. 运行测试
echo "[2/5] 运行测试..."
python -m pytest src/tests/ -q --tb=short 2>&1 | tail -5 || {
  echo "⚠️ 部分测试失败，继续构建..."
}

# 4. 清理旧构建
echo "[3/5] 清理旧构建..."
rm -rf build/ "$DIST_DIR"

# 5. PyInstaller 构建
echo "[4/5] PyInstaller 构建..."
pyinstaller config/charlie.spec \
  --distpath "$DIST_DIR" \
  --workpath build \
  --noconfirm 2>&1 | tail -10

# 6. 复制 .env（自用版含密钥）
echo "[5/5] 复制配置..."
if [ -f charlie/.env ]; then
  cp charlie/.env "$DIST_DIR/charlie/.env"
  echo "  ✓ .env → $DIST_DIR/charlie/.env"
fi

# 复制 ESP32 定制固件
if [ -d src/hardware/esp32_firmware/custom ]; then
  cp -r src/hardware/esp32_firmware/custom "$DIST_DIR/charlie/esp32_firmware/"
  echo "  ✓ ESP32 定制固件配置"
fi

# 7. 验证
echo ""
if [ -f "$DIST_DIR/charlie/charlie" ] || [ -f "$DIST_DIR/charlie/charlie.exe" ]; then
  SIZE=$(du -sh "$DIST_DIR/charlie" | cut -f1)
  echo "✅ CUSTOM 构建成功!"
  echo "   平台: $PLATFORM"
  echo "   大小: $SIZE"
  echo "   路径: $DIST_DIR/charlie/"
else
  echo "❌ 构建失败"
  exit 1
fi