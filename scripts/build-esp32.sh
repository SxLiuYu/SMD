#!/bin/bash
# build-esp32.sh — ESP32 固件构建（公版 + 定制版）
# 用法: bash scripts/build-esp32.sh [ootb|custom|all]
# 需要: ESP-IDF v5.1+ 环境
# 公版固件使用 xiaozhi-esp32 仓库，定制版需要本地 xz 仓库

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-ootb}"
DIST_DIR="dist/firmware"
mkdir -p "$DIST_DIR"

echo "🔧 ESP32 固件构建 — $MODE"
echo ""

build_ootb() {
  echo "=== 构建公版 OOTB 固件 ==="
  local XZ_DIR="${XZ_REPO:-../xiaozhi-esp32}"

  if [ ! -d "$XZ_DIR" ]; then
    echo "  ⚠️ 未找到 xiaozhi-esp32 仓库，跳过公版固件构建"
    echo "  git clone https://github.com/78/xiaozhi-esp32.git ../xiaozhi-esp32"
    return
  fi

  cd "$XZ_DIR"

  # 公版板型配置
  cat > sdkconfig.defaults << 'EOF'
CONFIG_BOARD_TYPE_XINGZHI_CUBE_1_54TFT_WIFI=y
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_OTA_URL="https://github.com/SxLiuYu/SMD-v2/releases/latest/download/firmware.bin"
EOF

  idf.py build
  cp build/bootloader/bootloader.bin "$ROOT/$DIST_DIR/"
  cp build/partition_table/partition-table.bin "$ROOT/$DIST_DIR/"
  cp build/charlie-esp32.bin "$ROOT/$DIST_DIR/"
  echo "  ✅ 公版固件构建完成"
  cd "$ROOT"
}

build_custom() {
  echo "=== 构建定制 LC-S3 固件 ==="
  local XZ_DIR="${XZ_REPO:-/Users/sxliuyu/repos/xz}"

  if [ ! -d "$XZ_DIR" ]; then
    echo "  ⚠️ 未找到 xz 仓库，跳过定制固件构建"
    return
  fi

  # 同步板型配置
  if [ -d src/hardware/esp32_firmware/custom ]; then
    cp src/hardware/esp32_firmware/custom/sdkconfig.lc-s3 "$XZ_DIR/sdkconfig"
    echo "  ✓ 同步 sdkconfig.lc-s3"
  fi

  cd "$XZ_DIR"
  idf.py build
  cp build/charlie-lc-s3.bin "$ROOT/$DIST_DIR/"
  echo "  ✅ 定制固件构建完成"
  cd "$ROOT"
}

case "$MODE" in
  ootb)  build_ootb ;;
  custom) build_custom ;;
  all)
    build_ootb
    build_custom
    ;;
  *)
    echo "用法: bash scripts/build-esp32.sh [ootb|custom|all]"
    exit 1
    ;;
esac

echo ""
echo "✅ 固件构建完成: $DIST_DIR/"